import json
import re
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import get_settings
from app.services.market_data import MarketQuote
from app.services.prompt_template import PROMPT_TEMPLATE

NUMERIC_FIELDS = [
    "current_price",
    "total_market_cap",
    "circulating_market_cap",
    "pe_dynamic",
    "pb",
    "gross_margin",
    "roe",
    "latest_profit_growth",
    "strong_support",
    "weak_support",
    "weak_resistance",
    "strong_resistance",
    "short_stop_loss",
    "short_take_profit",
    "buy_range_min",
    "buy_range_max",
    "sell_range_min",
    "sell_range_max",
    "turnover_rate",
]
TEXT_FIELDS = [
    "valuation_conclusion",
    "ai_action",
    "main_fund_flow",
    "core_theme",
    "short_term_catalyst",
    "main_risk",
    "report_markdown",
]


class DeepSeekService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def analyze(self, stock_code: str, stock_name: str, quote: MarketQuote) -> dict:
        prompt = PROMPT_TEMPLATE.format(
            stock_name=stock_name,
            stock_code=stock_code,
            analysis_time=datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
        )
        user_prompt = self._build_user_prompt(stock_code, stock_name, quote)
        payload = {
            "model": self.settings.deepseek_model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 4096,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.settings.deepseek_base_url.rstrip('/')}/chat/completions"
        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=self.settings.deepseek_timeout_seconds) as client:
            for _ in range(2):
                try:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    body = response.json()
                    choice = body["choices"][0]
                    content = choice["message"].get("content") or ""
                    finish_reason = choice.get("finish_reason")
                    parsed = await self._build_structured_payload(client, content, finish_reason)
                    parsed["provider"] = "deepseek"
                    parsed["raw_payload"] = content
                    return parsed
                except Exception as exc:
                    last_error = exc
        assert last_error is not None
        raise last_error

    def _build_user_prompt(self, stock_code: str, stock_name: str, quote: MarketQuote) -> str:
        return f"""
请基于上面的固定投研规则，对 {stock_name}（{stock_code}）做完整分析。

已知行情快照：
- 当前价格：{quote.current_price}
- 总市值：{quote.total_market_cap}
- 流通市值：{quote.circulating_market_cap}
- 动态PE：{quote.pe_dynamic}
- PB：{quote.pb}
- 换手率：{quote.turnover_rate}

请务必返回一个 JSON 对象，不要返回 markdown 包裹，不要返回解释文本。
JSON 字段必须包含：
- current_price: number|null
- total_market_cap: number|null
- circulating_market_cap: number|null
- pe_dynamic: number|null
- pb: number|null
- gross_margin: number|null
- roe: number|null
- latest_profit_growth: number|null
- strong_support: number|null
- weak_support: number|null
- weak_resistance: number|null
- strong_resistance: number|null
- short_stop_loss: number|null
- short_take_profit: number|null
- buy_range_min: number|null
- buy_range_max: number|null
- sell_range_min: number|null
- sell_range_max: number|null
- valuation_conclusion: string
- ai_action: string
- main_fund_flow: string
- turnover_rate: number|null
- core_theme: string
- short_term_catalyst: string
- main_risk: string
- report_markdown: string
"""

    async def _build_structured_payload(self, client: httpx.AsyncClient, content: str, finish_reason: str | None) -> dict:
        if not content.strip():
            raise ValueError("DeepSeek returned empty content")

        if finish_reason == "length":
            repaired = await self._repair_json_output(client, content)
            return self._normalize_payload(repaired)

        try:
            parsed = self._parse_json_payload(content)
        except json.JSONDecodeError:
            repaired = await self._repair_json_output(client, content)
            return self._normalize_payload(repaired)

        return self._normalize_payload(parsed)

    async def _repair_json_output(self, client: httpx.AsyncClient, malformed_content: str) -> dict:
        repair_prompt = """
You are repairing malformed stock-analysis json.
Return exactly one valid json object.
Use the same field names as provided.
If a field cannot be recovered, set it to null for numeric fields or an empty string for text fields.
Do not add markdown fences or explanations.
"""
        repair_schema = {
            "current_price": None,
            "total_market_cap": None,
            "circulating_market_cap": None,
            "pe_dynamic": None,
            "pb": None,
            "gross_margin": None,
            "roe": None,
            "latest_profit_growth": None,
            "strong_support": None,
            "weak_support": None,
            "weak_resistance": None,
            "strong_resistance": None,
            "short_stop_loss": None,
            "short_take_profit": None,
            "buy_range_min": None,
            "buy_range_max": None,
            "sell_range_min": None,
            "sell_range_max": None,
            "valuation_conclusion": "",
            "ai_action": "",
            "main_fund_flow": "",
            "turnover_rate": None,
            "core_theme": "",
            "short_term_catalyst": "",
            "main_risk": "",
            "report_markdown": "",
        }
        response = await client.post(
            f"{self.settings.deepseek_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.settings.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.settings.deepseek_model,
                "messages": [
                    {"role": "system", "content": repair_prompt},
                    {
                        "role": "user",
                        "content": (
                            "Please repair the following malformed json into a valid json object.\n"
                            f"Required schema example:\n{json.dumps(repair_schema, ensure_ascii=False)}\n"
                            f"Malformed content:\n{malformed_content}"
                        ),
                    },
                ],
                "temperature": 0,
                "max_tokens": 4096,
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"].get("content") or ""
        return self._parse_json_payload(content)

    @staticmethod
    def _parse_json_payload(content: str) -> dict:
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return parsed
            raise ValueError("Model response is not a JSON object")
        except json.JSONDecodeError:
            pass

        fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.DOTALL)
        if fenced_match:
            parsed = json.loads(fenced_match.group(1))
            if isinstance(parsed, dict):
                return parsed
            raise ValueError("Model fenced response is not a JSON object")

        object_match = re.search(r"(\{.*\})", content, re.DOTALL)
        if object_match:
            parsed = json.loads(object_match.group(1))
            if isinstance(parsed, dict):
                return parsed
            raise ValueError("Recovered response is not a JSON object")

        raise json.JSONDecodeError("Unable to parse JSON object from model response", content, 0)

    @classmethod
    def _normalize_payload(cls, payload: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}

        for field in NUMERIC_FIELDS:
            normalized[field] = cls._coerce_number(payload.get(field))

        for field in TEXT_FIELDS:
            normalized[field] = cls._coerce_text(payload.get(field))

        if not normalized["valuation_conclusion"]:
            normalized["valuation_conclusion"] = "待复核"
        if not normalized["ai_action"]:
            normalized["ai_action"] = "待复核"
        if not normalized["main_fund_flow"]:
            normalized["main_fund_flow"] = "未明确"
        if not normalized["core_theme"]:
            normalized["core_theme"] = "待补充"
        if not normalized["short_term_catalyst"]:
            normalized["short_term_catalyst"] = "待补充"
        if not normalized["main_risk"]:
            normalized["main_risk"] = "待补充"
        if not normalized["report_markdown"]:
            normalized["report_markdown"] = "模型没有返回完整报告，建议重试一次。"

        return normalized

    @staticmethod
    def _coerce_number(value: Any) -> float | None:
        if value is None or value == "":
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            cleaned = value.strip().replace(",", "").replace("，", "")
            cleaned = cleaned.replace("%", "").replace("％", "")
            if cleaned.lower() in {"null", "none", "nan", "--", "n/a", "暂无"}:
                return None
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None

    @staticmethod
    def _coerce_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return str(value).strip()
