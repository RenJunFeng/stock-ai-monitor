from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.database import Base, engine
from app.main import app


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
                {"stock_code": "600519", "stock_name": "\u8d35\u5dde\u8305\u53f0"},
                {"stock_code": "000001", "stock_name": "\u5e73\u5b89\u94f6\u884c"},
            ]
        },
    )
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = client.get("/api/watchlist")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_dashboard_endpoint_available():
    client = TestClient(app)
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    payload = response.json()
    assert "tracked_count" in payload
    assert "stocks" in payload
