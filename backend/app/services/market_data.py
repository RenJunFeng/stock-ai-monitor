import asyncio
import math
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from random import Random
from typing import Any, Optional

import requests

from app.core.config import get_settings

EASTMONEY_STOCK_URL = "https://82.push2.eastmoney.com/api/qt/stock/get"
EASTMONEY_SNAPSHOT_URL = "https://82.push2.eastmoney.com/api/qt/clist/get"
SINA_QUOTE_URL = "http://hq.sinajs.cn/list="
EASTMONEY_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://quote.eastmoney.com/",
}
SINA_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://finance.sina.com.cn/",
}
EASTMONEY_STOCK_FIELDS = ",".join(
    [
        "f43",   # 最新价 * 100
        "f44",   # 最高 * 100
        "f45",   # 最低 * 100
        "f46",   # 今开 * 100
        "f57",   # 代码
        "f58",   # 名称
        "f60",   # 昨收 * 100
        "f116",  # 总市值
        "f117",  # 流通市值
        "f162",  # 市盈率-动态 * 100
        "f167",  # 市净率 * 100
        "f168",  # 换手率 * 100
        "f169",  # 涨跌额 * 100
        "f170",  # 涨跌幅 * 100
    ]
)
EASTMONEY_SNAPSHOT_FIELDS = ",".join(
    [
        "f2",
        "f3",
        "f4",
        "f5",
        "f6",
        "f7",
        "f8",
        "f9",
        "f10",
        "f11",
        "f12",
        "f13",
        "f14",
        "f15",
        "f16",
        "f17",
        "f18",
        "f20",
        "f21",
        "f23",
        "f24",
        "f25",
        "f22",
        "f62",
        "f128",
        "f136",
        "f115",
        "f152",
    ]
)


@dataclass
class MarketQuote:
    stock_code: str
    stock_name: str
    current_price: float
    total_market_cap: Optional[float] = None
    circulating_market_cap: Optional[float] = None
    pe_dynamic: Optional[float] = None
    pb: Optional[float] = None
    turnover_rate: Optional[float] = None


class MarketDataService:
    _snapshot_cache: dict[str, dict[str, Any]] = {}
    _snapshot_cached_at: datetime | None = None
    _snapshot_ttl = timedelta(seconds=20)

    def __init__(self) -> None:
        self.settings = get_settings()

    async def get_quote(self, stock_code: str, stock_name: str) -> MarketQuote:
        provider = self.settings.market_provider.strip().lower()
        if provider == "sina":
            try:
                return await asyncio.to_thread(self._get_quote_with_sina_primary, stock_code, stock_name)
            except Exception:
                return self._mock_quote(stock_code, stock_name)
        if provider in {"eastmoney", "akshare"}:
            try:
                return await asyncio.to_thread(self._get_quote_with_live_sources, stock_code, stock_name)
            except Exception:
                return self._mock_quote(stock_code, stock_name)
        return self._mock_quote(stock_code, stock_name)

    def _mock_quote(self, stock_code: str, stock_name: str) -> MarketQuote:
        seed = int("".join(char for char in stock_code if char.isdigit()) or "1")
        rng = Random(seed)
        price = round(rng.uniform(8, 98), 2)
        return MarketQuote(
            stock_code=stock_code,
            stock_name=stock_name,
            current_price=price,
            total_market_cap=round(price * rng.uniform(12, 48), 2),
            circulating_market_cap=round(price * rng.uniform(8, 30), 2),
            pe_dynamic=round(rng.uniform(10, 45), 2),
            pb=round(rng.uniform(1, 8), 2),
            turnover_rate=round(rng.uniform(1, 18), 2),
        )

    def _get_quote_with_live_sources(self, stock_code: str, stock_name: str) -> MarketQuote:
        last_error: Exception | None = None
        try:
            base_quote = self._get_quote_with_sina(stock_code, stock_name)
        except Exception as exc:
            last_error = exc
            base_quote = None

        try:
            eastmoney_quote = self._get_quote_with_eastmoney(stock_code, stock_name)
        except Exception as exc:
            if last_error is None:
                last_error = exc
            eastmoney_quote = None

        if base_quote and eastmoney_quote:
            return self._merge_quotes(base_quote, eastmoney_quote)
        if base_quote:
            return base_quote
        if eastmoney_quote:
            return eastmoney_quote
        if last_error is not None:
            raise last_error
        raise LookupError("No realtime quote source returned data")

    def _get_quote_with_sina_primary(self, stock_code: str, stock_name: str) -> MarketQuote:
        try:
            return self._get_quote_with_sina(stock_code, stock_name)
        except Exception:
            return self._get_quote_with_eastmoney(stock_code, stock_name)

    def _get_quote_with_sina(self, stock_code: str, stock_name: str) -> MarketQuote:
        normalized_code = self._normalize_stock_code(stock_code)
        symbol = self._build_sina_symbol(normalized_code)
        response = requests.get(
            f"{SINA_QUOTE_URL}{symbol}",
            headers=SINA_HEADERS,
            timeout=12,
        )
        response.raise_for_status()
        response.encoding = "gbk"
        payload = response.text.strip()
        match = re.search(r'="(?P<body>.*)"\s*;?$', payload)
        if not match:
            raise ValueError(f"Unexpected Sina quote payload for {normalized_code}")

        parts = match.group("body").split(",")
        if len(parts) < 10 or not parts[0].strip():
            raise ValueError(f"Sina quote returned empty data for {normalized_code}")

        current_price = self._safe_float(parts[3])
        if current_price is None:
            raise ValueError(f"Sina quote missing current price for {normalized_code}")

        return MarketQuote(
            stock_code=normalized_code,
            stock_name=parts[0].strip() or stock_name,
            current_price=current_price,
        )

    def _get_quote_with_eastmoney(self, stock_code: str, stock_name: str) -> MarketQuote:
        normalized_code = self._normalize_stock_code(stock_code)

        for secid in self._build_secid_candidates(normalized_code):
            payload = self._fetch_single_quote(secid)
            if payload and str(payload.get("f57") or "") == normalized_code:
                return self._parse_single_quote(payload, stock_name)

        snapshot_row = self._get_snapshot_cache().get(normalized_code)
        if snapshot_row:
            return self._parse_snapshot_row(snapshot_row, stock_name)

        raise LookupError(f"Unable to fetch realtime market quote for {normalized_code}")

    def _fetch_single_quote(self, secid: str) -> dict[str, Any] | None:
        response = self._request_json(
            EASTMONEY_STOCK_URL,
            {
                "secid": secid,
                "ut": "f057cbcbce2a86e2866ab8877db1d059",
                "fields": EASTMONEY_STOCK_FIELDS,
            },
        )
        data = response.get("data")
        if not isinstance(data, dict) or not data.get("f57"):
            return None
        return data

    @classmethod
    def _get_snapshot_cache(cls) -> dict[str, dict[str, Any]]:
        now = datetime.now(UTC)
        if cls._snapshot_cache and cls._snapshot_cached_at and now - cls._snapshot_cached_at < cls._snapshot_ttl:
            return cls._snapshot_cache

        first_page = cls._fetch_snapshot_page(1)
        data = first_page.get("data") or {}
        total = int(data.get("total") or 0)
        diff = list(data.get("diff") or [])
        if total <= 0 or not diff:
            raise LookupError("Eastmoney snapshot returned no data")

        page_size = len(diff)
        total_pages = math.ceil(total / page_size)
        all_rows = diff[:]

        if total_pages > 1:
            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = [executor.submit(cls._fetch_snapshot_page, page) for page in range(2, total_pages + 1)]
                for future in as_completed(futures):
                    page_data = future.result().get("data") or {}
                    all_rows.extend(page_data.get("diff") or [])

        cls._snapshot_cache = {
            str(row.get("f12")): row
            for row in all_rows
            if isinstance(row, dict) and row.get("f12")
        }
        cls._snapshot_cached_at = now
        return cls._snapshot_cache

    @classmethod
    def _fetch_snapshot_page(cls, page: int) -> dict[str, Any]:
        return cls._request_json(
            EASTMONEY_SNAPSHOT_URL,
            {
                "pn": str(page),
                "pz": "100",
                "po": "1",
                "np": "1",
                "ut": "bd1d9ddb04089700cf9c27f6f7426281",
                "fltt": "2",
                "invt": "2",
                "fid": "f12",
                "fs": "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048",
                "fields": EASTMONEY_SNAPSHOT_FIELDS,
            },
        )

    @staticmethod
    def _request_json(url: str, params: dict[str, str]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = requests.get(url, params=params, headers=EASTMONEY_HEADERS, timeout=12)
                response.raise_for_status()
                payload = response.json()
                if payload.get("rc") not in (0, None):
                    raise ValueError(f"Eastmoney returned rc={payload.get('rc')}")
                return payload
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(0.6 * (attempt + 1))
        assert last_error is not None
        raise last_error

    @classmethod
    def _parse_single_quote(cls, payload: dict[str, Any], fallback_name: str) -> MarketQuote:
        return MarketQuote(
            stock_code=str(payload.get("f57") or "").strip(),
            stock_name=str(payload.get("f58") or fallback_name),
            current_price=cls._scaled_float(payload.get("f43"), 100) or 0.0,
            total_market_cap=cls._safe_float(payload.get("f116")),
            circulating_market_cap=cls._safe_float(payload.get("f117")),
            pe_dynamic=cls._scaled_float(payload.get("f162"), 100),
            pb=cls._scaled_float(payload.get("f167"), 100),
            turnover_rate=cls._scaled_float(payload.get("f168"), 100),
        )

    @classmethod
    def _parse_snapshot_row(cls, row: dict[str, Any], fallback_name: str) -> MarketQuote:
        return MarketQuote(
            stock_code=str(row.get("f12") or "").strip(),
            stock_name=str(row.get("f14") or fallback_name),
            current_price=cls._safe_float(row.get("f2")) or 0.0,
            total_market_cap=cls._safe_float(row.get("f20")),
            circulating_market_cap=cls._safe_float(row.get("f21")),
            pe_dynamic=cls._safe_float(row.get("f9")),
            pb=cls._safe_float(row.get("f23")),
            turnover_rate=cls._safe_float(row.get("f8")),
        )

    @staticmethod
    def _merge_quotes(primary: MarketQuote, supplement: MarketQuote) -> MarketQuote:
        return MarketQuote(
            stock_code=primary.stock_code or supplement.stock_code,
            stock_name=primary.stock_name or supplement.stock_name,
            current_price=primary.current_price or supplement.current_price,
            total_market_cap=primary.total_market_cap if primary.total_market_cap is not None else supplement.total_market_cap,
            circulating_market_cap=(
                primary.circulating_market_cap
                if primary.circulating_market_cap is not None
                else supplement.circulating_market_cap
            ),
            pe_dynamic=primary.pe_dynamic if primary.pe_dynamic is not None else supplement.pe_dynamic,
            pb=primary.pb if primary.pb is not None else supplement.pb,
            turnover_rate=primary.turnover_rate if primary.turnover_rate is not None else supplement.turnover_rate,
        )

    @staticmethod
    def _normalize_stock_code(stock_code: str) -> str:
        return "".join(char for char in stock_code if char.isdigit())

    @staticmethod
    def _build_sina_symbol(stock_code: str) -> str:
        if stock_code.startswith(("600", "601", "603", "605", "688", "689", "900", "510", "511", "512", "513", "515")):
            return f"sh{stock_code}"
        if stock_code.startswith(("000", "001", "002", "003", "159", "200", "300", "301")):
            return f"sz{stock_code}"
        if stock_code.startswith(("4", "8", "920")):
            return f"bj{stock_code}"
        raise ValueError(f"Unsupported Sina quote symbol: {stock_code}")

    @classmethod
    def _build_secid_candidates(cls, stock_code: str) -> list[str]:
        if stock_code.startswith(("600", "601", "603", "605", "688", "689", "900", "510", "511", "512", "513", "515")):
            prefixes = ["1"]
        elif stock_code.startswith(("000", "001", "002", "003", "159", "200", "300", "301")):
            prefixes = ["0"]
        elif stock_code.startswith(("4", "8", "920")):
            prefixes = ["0", "1"]
        else:
            prefixes = ["0", "1"]
        return [f"{prefix}.{stock_code}" for prefix in prefixes]

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _scaled_float(cls, value: Any, divisor: float) -> Optional[float]:
        numeric = cls._safe_float(value)
        if numeric is None:
            return None
        return numeric / divisor
