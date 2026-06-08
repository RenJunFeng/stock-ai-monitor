from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import AlertLog, StockAnalysis, WatchlistStock
from app.services.alert_service import AlertService
from app.services.deepseek_service import DeepSeekService
from app.services.market_data import MarketDataService
from app.services.mock_analysis import build_mock_analysis


class AnalysisService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.market_data = MarketDataService()
        self.deepseek = DeepSeekService()
        self.alert_service = AlertService()

    async def run_for_watchlist(self, db: Session, stock_codes: list[str] | None = None, manual_trigger: bool = False) -> list[StockAnalysis]:
        query = select(WatchlistStock).order_by(WatchlistStock.stock_code.asc())
        if stock_codes:
            query = query.where(WatchlistStock.stock_code.in_(stock_codes))
        stocks = db.execute(query).scalars().all()

        results: list[StockAnalysis] = []
        for stock in stocks:
            try:
                analysis = await self._analyze_one(stock.stock_code, stock.stock_name, manual_trigger)
            except Exception as exc:
                analysis = self._build_failed_analysis(stock.stock_code, stock.stock_name, manual_trigger, str(exc))
            db.add(analysis)
            db.flush()

            try:
                for alert in self.alert_service.evaluate(analysis):
                    db.add(alert)
            except Exception:
                pass

            results.append(analysis)

        db.commit()
        for item in results:
            db.refresh(item)
        return results

    async def _analyze_one(self, stock_code: str, stock_name: str, manual_trigger: bool) -> StockAnalysis:
        quote = await self.market_data.get_quote(stock_code, stock_name)
        if self.settings.deepseek_ready:
            try:
                payload = await self.deepseek.analyze(stock_code, stock_name, quote)
            except Exception:
                payload = build_mock_analysis(stock_code, stock_name, quote)
        else:
            payload = build_mock_analysis(stock_code, stock_name, quote)

        payload = self._apply_realtime_market_snapshot(payload, quote)

        return StockAnalysis(
            stock_code=stock_code,
            stock_name=stock_name,
            provider=payload.get("provider", "mock"),
            manual_trigger=manual_trigger,
            current_price=payload.get("current_price"),
            total_market_cap=payload.get("total_market_cap"),
            circulating_market_cap=payload.get("circulating_market_cap"),
            pe_dynamic=payload.get("pe_dynamic"),
            pb=payload.get("pb"),
            gross_margin=payload.get("gross_margin"),
            roe=payload.get("roe"),
            latest_profit_growth=payload.get("latest_profit_growth"),
            strong_support=payload.get("strong_support"),
            weak_support=payload.get("weak_support"),
            weak_resistance=payload.get("weak_resistance"),
            strong_resistance=payload.get("strong_resistance"),
            short_stop_loss=payload.get("short_stop_loss"),
            short_take_profit=payload.get("short_take_profit"),
            buy_range_min=payload.get("buy_range_min"),
            buy_range_max=payload.get("buy_range_max"),
            sell_range_min=payload.get("sell_range_min"),
            sell_range_max=payload.get("sell_range_max"),
            valuation_conclusion=payload.get("valuation_conclusion"),
            ai_action=payload.get("ai_action"),
            main_fund_flow=payload.get("main_fund_flow"),
            turnover_rate=payload.get("turnover_rate"),
            core_theme=payload.get("core_theme"),
            short_term_catalyst=payload.get("short_term_catalyst"),
            main_risk=payload.get("main_risk"),
            report_markdown=payload.get("report_markdown", ""),
            raw_payload=payload.get("raw_payload"),
        )

    @staticmethod
    def _apply_realtime_market_snapshot(payload: dict, quote) -> dict:
        merged = dict(payload)
        merged["current_price"] = quote.current_price
        merged["total_market_cap"] = quote.total_market_cap
        merged["circulating_market_cap"] = quote.circulating_market_cap
        merged["pe_dynamic"] = quote.pe_dynamic
        merged["pb"] = quote.pb
        merged["turnover_rate"] = quote.turnover_rate
        return merged

    @staticmethod
    def _build_failed_analysis(stock_code: str, stock_name: str, manual_trigger: bool, error_message: str) -> StockAnalysis:
        fallback_report = (
            "## 本轮分析未完全成功\n\n"
            f"- 股票：{stock_name} ({stock_code})\n"
            "- 系统已跳过本只股票的异常结果，避免整轮分析中断。\n"
            f"- 错误摘要：{error_message[:300]}\n"
        )
        return StockAnalysis(
            stock_code=stock_code,
            stock_name=stock_name,
            provider="fallback",
            manual_trigger=manual_trigger,
            valuation_conclusion="待复核",
            ai_action="待复核",
            main_fund_flow="未获取",
            core_theme="本轮分析异常",
            short_term_catalyst="待重试",
            main_risk="模型或数据源返回异常",
            report_markdown=fallback_report,
            raw_payload=error_message[:2000],
        )

    def get_latest_analyses(self, db: Session) -> list[StockAnalysis]:
        stocks = db.execute(select(WatchlistStock).order_by(WatchlistStock.stock_code.asc())).scalars().all()
        latest: list[StockAnalysis] = []
        for stock in stocks:
            analysis = db.execute(
                select(StockAnalysis)
                .where(StockAnalysis.stock_code == stock.stock_code)
                .order_by(desc(StockAnalysis.analysis_time))
                .limit(1)
            ).scalar_one_or_none()
            if analysis:
                latest.append(analysis)
        return latest

    def clear_all_analyses(self, db: Session) -> None:
        db.execute(delete(StockAnalysis))
        db.execute(delete(AlertLog))
        db.commit()
