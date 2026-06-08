from datetime import UTC, datetime
from random import Random

from app.services.market_data import MarketQuote


def build_mock_analysis(stock_code: str, stock_name: str, quote: MarketQuote) -> dict:
    seed = int("".join(char for char in stock_code if char.isdigit()) or "1")
    rng = Random(seed)
    buy_min = round(max(1, quote.current_price * rng.uniform(0.92, 0.97)), 2)
    buy_max = round(quote.current_price * rng.uniform(0.98, 1.01), 2)
    sell_min = round(quote.current_price * rng.uniform(1.03, 1.07), 2)
    sell_max = round(quote.current_price * rng.uniform(1.08, 1.16), 2)
    action = ["重点买入", "持有观望", "逢高减仓", "坚决规避"][seed % 4]
    valuation = ["低估", "合理", "高估"][seed % 3]
    analysis_time = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    report = f"""# {stock_name}（{stock_code}）AI 分析报告

## 一、个股基础概况
- 所属赛道：高景气成长或周期修复方向。
- 当前价格：{quote.current_price} 元。
- 总市值：{quote.total_market_cap or 0} 亿元。

## 二、基本面
- 动态 PE：{quote.pe_dynamic or 0}
- PB：{quote.pb or 0}
- 毛利率：{round(rng.uniform(18, 48), 2)}%
- ROE：{round(rng.uniform(8, 22), 2)}%
- 最新财报净利润增速：{round(rng.uniform(-8, 38), 2)}%

## 三、技术面
- 强支撑：{round(buy_min * 0.97, 2)}
- 弱支撑：{buy_min}
- 弱压力：{sell_min}
- 强压力：{sell_max}
- 止损：{round(buy_min * 0.95, 2)}
- 止盈：{round(sell_max * 1.02, 2)}

## 四、资金与情绪
- 主力资金：近三个交易日呈现温和流入。
- 换手率：{quote.turnover_rate or 0}%
- 核心题材：AI+高股息+景气修复

## 五、估值结论
- 当前估值判断：{valuation}

## 六、风险与催化
- 催化：业绩预增、行业政策、订单落地。
- 风险：行业波动、业绩兑现低于预期、短线情绪回落。

## 七、操作策略
- 买入区间：{buy_min} - {buy_max}
- 卖出区间：{sell_min} - {sell_max}
- 核心建议：{action}

## 八、免责声明
本内容为 mock 分析，仅供系统联调与演示使用，不构成投资建议。

分析时间：{analysis_time}
"""

    return {
        "provider": "mock",
        "current_price": quote.current_price,
        "total_market_cap": quote.total_market_cap,
        "circulating_market_cap": quote.circulating_market_cap,
        "pe_dynamic": quote.pe_dynamic,
        "pb": quote.pb,
        "gross_margin": round(rng.uniform(18, 48), 2),
        "roe": round(rng.uniform(8, 22), 2),
        "latest_profit_growth": round(rng.uniform(-8, 38), 2),
        "strong_support": round(buy_min * 0.97, 2),
        "weak_support": buy_min,
        "weak_resistance": sell_min,
        "strong_resistance": sell_max,
        "short_stop_loss": round(buy_min * 0.95, 2),
        "short_take_profit": round(sell_max * 1.02, 2),
        "buy_range_min": buy_min,
        "buy_range_max": buy_max,
        "sell_range_min": sell_min,
        "sell_range_max": sell_max,
        "valuation_conclusion": valuation,
        "ai_action": action,
        "main_fund_flow": "近三日净流入",
        "turnover_rate": quote.turnover_rate,
        "core_theme": "AI, 国企改革, 高股息",
        "short_term_catalyst": "财报披露窗口、行业政策催化、增持回购预期",
        "main_risk": "短线波动放大、成交量不足、业绩兑现不及预期",
        "report_markdown": report,
        "raw_payload": report,
    }
