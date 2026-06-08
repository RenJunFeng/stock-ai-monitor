from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import AlertLog, StockAnalysis, WatchlistStock
from app.schemas import AlertRead, AnalysisRead, AnalysisRunRequest, DashboardOverview, WatchlistBatchCreate, WatchlistItemRead
from app.services.analysis_service import AnalysisService


router = APIRouter()
analysis_service = AnalysisService()


@router.get("/health")
def healthcheck():
    return {"status": "ok", "timestamp": datetime.now(UTC).isoformat()}


@router.get("/watchlist", response_model=list[WatchlistItemRead])
def list_watchlist(db: Session = Depends(get_db)):
    return db.execute(select(WatchlistStock).order_by(WatchlistStock.created_at.asc())).scalars().all()


@router.post("/watchlist", response_model=list[WatchlistItemRead])
def create_watchlist(payload: WatchlistBatchCreate, db: Session = Depends(get_db)):
    existing_codes = {
        stock.stock_code
        for stock in db.execute(select(WatchlistStock).where(WatchlistStock.stock_code.in_([item.stock_code for item in payload.items]))).scalars().all()
    }
    created: list[WatchlistStock] = []
    for item in payload.items:
        if item.stock_code in existing_codes:
            continue
        stock = WatchlistStock(stock_code=item.stock_code, stock_name=item.stock_name)
        db.add(stock)
        created.append(stock)
    db.commit()
    for item in created:
        db.refresh(item)
    return db.execute(select(WatchlistStock).order_by(WatchlistStock.created_at.asc())).scalars().all()


@router.delete("/watchlist/{stock_id}")
def delete_watchlist_item(stock_id: int, db: Session = Depends(get_db)):
    stock = db.get(WatchlistStock, stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail="股票不存在。")
    db.delete(stock)
    db.commit()
    return {"success": True}


@router.delete("/watchlist")
def clear_watchlist(db: Session = Depends(get_db)):
    db.execute(delete(WatchlistStock))
    db.commit()
    return {"success": True}


@router.post("/analysis/run", response_model=list[AnalysisRead])
async def run_analysis(payload: AnalysisRunRequest, db: Session = Depends(get_db)):
    return await analysis_service.run_for_watchlist(db, stock_codes=payload.stock_codes, manual_trigger=payload.manual_trigger)


@router.get("/analysis/latest", response_model=list[AnalysisRead])
def get_latest_analysis(db: Session = Depends(get_db)):
    return analysis_service.get_latest_analyses(db)


@router.get("/analysis/{stock_code}/latest", response_model=AnalysisRead)
def get_stock_latest_analysis(stock_code: str, db: Session = Depends(get_db)):
    analysis = db.execute(
        select(StockAnalysis)
        .where(StockAnalysis.stock_code == stock_code)
        .order_by(desc(StockAnalysis.analysis_time))
        .limit(1)
    ).scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="该股票暂无分析结果。")
    return analysis


@router.get("/alerts", response_model=list[AlertRead])
def list_alerts(stock_code: str | None = None, start_at: str | None = None, end_at: str | None = None, db: Session = Depends(get_db)):
    query = select(AlertLog).order_by(desc(AlertLog.created_at))
    if stock_code:
        query = query.where(AlertLog.stock_code == stock_code)
    if start_at:
        query = query.where(AlertLog.created_at >= datetime.fromisoformat(start_at))
    if end_at:
        query = query.where(AlertLog.created_at <= datetime.fromisoformat(end_at))
    return db.execute(query).scalars().all()


@router.get("/dashboard", response_model=DashboardOverview)
def dashboard(db: Session = Depends(get_db)):
    latest = analysis_service.get_latest_analyses(db)
    alerts = db.execute(select(AlertLog).order_by(desc(AlertLog.created_at)).limit(10)).scalars().all()
    breakdown_map: dict[str, int] = {}
    for item in latest:
        key = item.ai_action or "未分类"
        breakdown_map[key] = breakdown_map.get(key, 0) + 1
    breakdown = [{"name": key, "value": value} for key, value in breakdown_map.items()]

    return DashboardOverview(
        tracked_count=db.query(WatchlistStock).count(),
        latest_analysis_count=len(latest),
        recommendation_breakdown=breakdown,
        latest_alerts=alerts,
        stocks=latest,
    )
