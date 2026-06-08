from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class WatchlistStock(Base):
    __tablename__ = "watchlist_stocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    stock_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    stock_name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class StockAnalysis(Base):
    __tablename__ = "stock_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    stock_code: Mapped[str] = mapped_column(String(20), index=True)
    stock_name: Mapped[str] = mapped_column(String(100))
    provider: Mapped[str] = mapped_column(String(50), default="mock")
    analysis_time: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    manual_trigger: Mapped[bool] = mapped_column(Boolean, default=False)

    current_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
    circulating_market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
    pe_dynamic: Mapped[float | None] = mapped_column(Float, nullable=True)
    pb: Mapped[float | None] = mapped_column(Float, nullable=True)
    gross_margin: Mapped[float | None] = mapped_column(Float, nullable=True)
    roe: Mapped[float | None] = mapped_column(Float, nullable=True)
    latest_profit_growth: Mapped[float | None] = mapped_column(Float, nullable=True)
    strong_support: Mapped[float | None] = mapped_column(Float, nullable=True)
    weak_support: Mapped[float | None] = mapped_column(Float, nullable=True)
    weak_resistance: Mapped[float | None] = mapped_column(Float, nullable=True)
    strong_resistance: Mapped[float | None] = mapped_column(Float, nullable=True)
    short_stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    short_take_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    buy_range_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    buy_range_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    sell_range_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    sell_range_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    valuation_conclusion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_action: Mapped[str | None] = mapped_column(String(50), nullable=True)
    main_fund_flow: Mapped[str | None] = mapped_column(String(100), nullable=True)
    turnover_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    core_theme: Mapped[str | None] = mapped_column(String(200), nullable=True)
    short_term_catalyst: Mapped[str | None] = mapped_column(String(300), nullable=True)
    main_risk: Mapped[str | None] = mapped_column(String(300), nullable=True)
    report_markdown: Mapped[str] = mapped_column(Text)
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)


class AlertLog(Base):
    __tablename__ = "alert_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    stock_code: Mapped[str] = mapped_column(String(20), index=True)
    stock_name: Mapped[str] = mapped_column(String(100))
    trigger_type: Mapped[str] = mapped_column(String(50), index=True)
    current_price: Mapped[float] = mapped_column(Float)
    ai_action: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email_status: Mapped[str] = mapped_column(String(50), default="pending")
    email_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
