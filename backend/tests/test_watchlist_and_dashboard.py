from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.database import Base, engine
from app.main import app
from app.models import StockAnalysis


def setup_module():
    settings = get_settings()
    assert settings.deepseek_model == "deepseek-v4-pro"
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_watchlist_create_and_list():
    client = TestClient(app)

    response = client.post(
        "/api/watchlist",
        json={
            "items": [
                {"stock_code": "600519", "stock_name": "\u8d35\u5dde\u8305\u53f0", "group_name": "\u767d\u9152"},
                {"stock_code": "000001", "stock_name": "\u5e73\u5b89\u94f6\u884c", "group_name": "\u94f6\u884c"},
            ]
        },
    )
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = client.get("/api/watchlist")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert {item["group_name"] for item in data} >= {"\u767d\u9152", "\u94f6\u884c"}


def test_watchlist_existing_code_updates_group():
    client = TestClient(app)

    response = client.post(
        "/api/watchlist",
        json={"items": [{"stock_code": "600519", "stock_name": "\u8d35\u5dde\u8305\u53f0", "group_name": "\u9ad8\u7aef\u6d88\u8d39"}]},
    )

    assert response.status_code == 200
    updated = next(item for item in response.json() if item["stock_code"] == "600519")
    assert updated["group_name"] == "\u9ad8\u7aef\u6d88\u8d39"


def test_analysis_run_can_target_group(monkeypatch):
    client = TestClient(app)

    async def fake_analyze_one(stock_code: str, stock_name: str, manual_trigger: bool) -> StockAnalysis:
        return StockAnalysis(
            stock_code=stock_code,
            stock_name=stock_name,
            provider="test",
            manual_trigger=manual_trigger,
            report_markdown="ok",
        )

    from app.api import analysis_service

    monkeypatch.setattr(analysis_service, "_analyze_one", fake_analyze_one)
    response = client.post("/api/analysis/run", json={"manual_trigger": True, "group_name": "\u94f6\u884c"})

    assert response.status_code == 200
    payload = response.json()
    assert [item["stock_code"] for item in payload] == ["000001"]


def test_dashboard_endpoint_available():
    client = TestClient(app)
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    payload = response.json()
    assert "tracked_count" in payload
    assert "stocks" in payload
