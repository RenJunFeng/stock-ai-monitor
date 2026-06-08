from app.services.deepseek_service import DeepSeekService


def test_parse_json_payload_accepts_fenced_json():
    content = """
```json
{"ai_action":"观察","valuation_conclusion":"中性","report_markdown":"ok"}
```
"""

    parsed = DeepSeekService._parse_json_payload(content)

    assert parsed["ai_action"] == "观察"
    assert parsed["valuation_conclusion"] == "中性"


def test_normalize_payload_coerces_strings_and_fills_missing_fields():
    payload = {
        "current_price": "11.08",
        "turnover_rate": "0.32%",
        "valuation_conclusion": "",
        "ai_action": None,
        "main_fund_flow": None,
        "report_markdown": "",
    }

    normalized = DeepSeekService._normalize_payload(payload)

    assert normalized["current_price"] == 11.08
    assert normalized["turnover_rate"] == 0.32
    assert normalized["valuation_conclusion"] == "待复核"
    assert normalized["ai_action"] == "待复核"
    assert normalized["main_fund_flow"] == "未明确"
    assert normalized["report_markdown"] == "模型没有返回完整报告，建议重试一次。"
