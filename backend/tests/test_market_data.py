from app.services.market_data import MarketDataService


def test_build_secid_candidates_for_common_a_shares():
    assert MarketDataService._build_secid_candidates("600519") == ["1.600519"]
    assert MarketDataService._build_secid_candidates("000001") == ["0.000001"]
    assert MarketDataService._build_secid_candidates("300750") == ["0.300750"]


def test_build_sina_symbol_for_common_a_shares():
    assert MarketDataService._build_sina_symbol("600519") == "sh600519"
    assert MarketDataService._build_sina_symbol("000001") == "sz000001"
    assert MarketDataService._build_sina_symbol("300750") == "sz300750"


def test_parse_single_quote_payload():
    payload = {
        "f43": 126574,
        "f57": "600519",
        "f58": "贵州茅台",
        "f116": 1582278285649.74,
        "f117": 1582278285649.74,
        "f162": 1452,
        "f167": 584,
        "f168": 15,
    }

    quote = MarketDataService._parse_single_quote(payload, "备用名称")

    assert quote.stock_code == "600519"
    assert quote.stock_name == "贵州茅台"
    assert quote.current_price == 1265.74
    assert quote.total_market_cap == 1582278285649.74
    assert quote.circulating_market_cap == 1582278285649.74
    assert quote.pe_dynamic == 14.52
    assert quote.pb == 5.84
    assert quote.turnover_rate == 0.15


def test_snapshot_fallback_reads_eastmoney_grid_row(monkeypatch):
    service = MarketDataService()

    monkeypatch.setattr(service, "_fetch_single_quote", lambda secid: None)
    monkeypatch.setattr(
        service,
        "_get_snapshot_cache",
        lambda: {
            "000001": {
                "f12": "000001",
                "f14": "平安银行",
                "f2": 11.23,
                "f20": 217966004606.96,
                "f21": 217963438650.92,
                "f9": 5.73,
                "f23": 0.62,
                "f8": 0.65,
            }
        },
    )

    quote = service._get_quote_with_eastmoney("000001", "平安银行")

    assert quote.stock_code == "000001"
    assert quote.stock_name == "平安银行"
    assert quote.current_price == 11.23
    assert quote.total_market_cap == 217966004606.96
    assert quote.circulating_market_cap == 217963438650.92
    assert quote.pe_dynamic == 5.73
    assert quote.pb == 0.62
    assert quote.turnover_rate == 0.65
