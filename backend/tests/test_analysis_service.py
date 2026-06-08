from app.services.analysis_service import AnalysisService
from app.services.market_data import MarketQuote


def test_realtime_market_snapshot_overrides_model_numbers():
    quote = MarketQuote(
        stock_code="600519",
        stock_name="贵州茅台",
        current_price=1265.74,
        total_market_cap=1582278285649.74,
        circulating_market_cap=1582278285649.74,
        pe_dynamic=14.52,
        pb=5.84,
        turnover_rate=0.15,
    )
    payload = {
        "provider": "deepseek",
        "current_price": 40.39,
        "total_market_cap": 1070.1,
        "circulating_market_cap": 950.0,
        "pe_dynamic": 22.0,
        "pb": 2.1,
        "turnover_rate": 15.02,
    }

    merged = AnalysisService._apply_realtime_market_snapshot(payload, quote)

    assert merged["provider"] == "deepseek"
    assert merged["current_price"] == 1265.74
    assert merged["total_market_cap"] == 1582278285649.74
    assert merged["circulating_market_cap"] == 1582278285649.74
    assert merged["pe_dynamic"] == 14.52
    assert merged["pb"] == 5.84
    assert merged["turnover_rate"] == 0.15
