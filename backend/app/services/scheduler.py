import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.analysis_service import AnalysisService


class SchedulerService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.scheduler = AsyncIOScheduler()
        self.analysis_service = AnalysisService()

    def start(self) -> None:
        if not self.settings.scheduler_enabled:
            return
        self.scheduler.add_job(
            self._run_job,
            trigger="interval",
            minutes=self.settings.scheduler_interval_minutes,
            id="hourly-stock-analysis",
            replace_existing=True,
        )
        self.scheduler.start()

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def _run_job(self) -> None:
        asyncio.create_task(self._run_async_job())

    async def _run_async_job(self) -> None:
        db = SessionLocal()
        try:
            await self.analysis_service.run_for_watchlist(db=db, manual_trigger=False)
        finally:
            db.close()

