from collections.abc import Iterable

from app.models import AlertLog, StockAnalysis
from app.services.email_service import EmailService


class AlertService:
    def __init__(self) -> None:
        self.email_service = EmailService()

    def evaluate(self, analysis: StockAnalysis) -> list[AlertLog]:
        triggers = list(self._detect_triggers(analysis))
        results: list[AlertLog] = []

        for trigger in triggers:
            subject = f"[股票监控告警] {analysis.stock_name} {analysis.stock_code} - {trigger}"
            body = (
                f"股票：{analysis.stock_name} ({analysis.stock_code})\n"
                f"触发类型：{trigger}\n"
                f"当前价格：{analysis.current_price}\n"
                f"AI 建议：{analysis.ai_action or '未提供'}\n"
            )
            status, error = self.email_service.send_alert(subject, body)
            results.append(
                AlertLog(
                    stock_code=analysis.stock_code,
                    stock_name=analysis.stock_name,
                    trigger_type=trigger,
                    current_price=analysis.current_price or 0,
                    ai_action=analysis.ai_action,
                    email_status=status,
                    email_error=error,
                )
            )
        return results

    def _detect_triggers(self, analysis: StockAnalysis) -> Iterable[str]:
        if analysis.current_price is None:
            return []

        price = analysis.current_price
        if analysis.buy_range_min is not None and analysis.buy_range_max is not None:
            if analysis.buy_range_min <= price <= analysis.buy_range_max:
                yield "buy-range"
        if analysis.sell_range_min is not None and analysis.sell_range_max is not None:
            if analysis.sell_range_min <= price <= analysis.sell_range_max:
                yield "sell-range"
        if analysis.short_stop_loss is not None and price <= analysis.short_stop_loss:
            yield "stop-loss"
        if analysis.short_take_profit is not None and price >= analysis.short_take_profit:
            yield "take-profit"

