from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class WatchlistItemCreate(BaseModel):
    stock_code: str = Field(min_length=6, max_length=20)
    stock_name: str = Field(min_length=1, max_length=100)

    @field_validator("stock_code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip()

    @field_validator("stock_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()


class WatchlistBatchCreate(BaseModel):
    items: list[WatchlistItemCreate]

    @field_validator("items")
    @classmethod
    def validate_batch_size(cls, value: list[WatchlistItemCreate]) -> list[WatchlistItemCreate]:
        if not value:
            raise ValueError("至少需要一只股票。")
        if len(value) > 10:
            raise ValueError("单次最多提交 10 只股票。")
        return value


class WatchlistItemRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    stock_code: str
    stock_name: str
    created_at: datetime
    updated_at: datetime


class AnalysisRunRequest(BaseModel):
    stock_codes: Optional[list[str]] = None
    manual_trigger: bool = True


class AnalysisRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    stock_code: str
    stock_name: str
    provider: str
    analysis_time: datetime
    manual_trigger: bool
    current_price: Optional[float] = None
    total_market_cap: Optional[float] = None
    circulating_market_cap: Optional[float] = None
    pe_dynamic: Optional[float] = None
    pb: Optional[float] = None
    gross_margin: Optional[float] = None
    roe: Optional[float] = None
    latest_profit_growth: Optional[float] = None
    strong_support: Optional[float] = None
    weak_support: Optional[float] = None
    weak_resistance: Optional[float] = None
    strong_resistance: Optional[float] = None
    short_stop_loss: Optional[float] = None
    short_take_profit: Optional[float] = None
    buy_range_min: Optional[float] = None
    buy_range_max: Optional[float] = None
    sell_range_min: Optional[float] = None
    sell_range_max: Optional[float] = None
    valuation_conclusion: Optional[str] = None
    ai_action: Optional[str] = None
    main_fund_flow: Optional[str] = None
    turnover_rate: Optional[float] = None
    core_theme: Optional[str] = None
    short_term_catalyst: Optional[str] = None
    main_risk: Optional[str] = None
    report_markdown: str


class AlertRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    stock_code: str
    stock_name: str
    trigger_type: str
    current_price: float
    ai_action: Optional[str] = None
    email_status: str
    email_error: Optional[str] = None
    created_at: datetime


class DashboardOverview(BaseModel):
    tracked_count: int
    latest_analysis_count: int
    recommendation_breakdown: list[dict[str, Any]]
    latest_alerts: list[AlertRead]
    stocks: list[AnalysisRead]

