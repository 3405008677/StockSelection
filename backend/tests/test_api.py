from fastapi.testclient import TestClient
import pytest

from app import services
from app.main import app
from app.models import Market
from app.sample_data import CN_STOCKS, US_STOCKS, generate_daily, generate_intraday


client = TestClient(app)


@pytest.fixture(autouse=True)
def offline_data_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_universe(market: Market, limit: int | None = None):
        return CN_STOCKS if market == Market.cn else US_STOCKS

    def fake_daily(market: Market, symbol: str, days: int = 90):
        return generate_daily(100, 0.5)

    def fake_intraday(market: Market, symbol: str):
        return generate_intraday(100)

    monkeypatch.setattr(services, "fetch_universe", fake_universe)
    monkeypatch.setattr(services, "fetch_daily", fake_daily)
    monkeypatch.setattr(services, "fetch_intraday", fake_intraday)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_screen_and_detail_flow() -> None:
    with client:
        response = client.post(
            "/api/screen/run",
            json={
                "market": "cn",
                "conditions": [
                    {"indicator": "ma", "period": 5, "operator": ">", "value": 1, "enabled": True},
                    {"indicator": "rsi", "period": 14, "operator": ">", "value": 10, "enabled": True},
                ],
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["results"]
        symbol = body["results"][0]["symbol"]
        detail = client.get(f"/api/stocks/cn/{symbol}")
        assert detail.status_code == 200
        assert detail.json()["stock"]["symbol"] == symbol


def test_watchlist_and_template_flow() -> None:
    with client:
        item = client.post("/api/watchlists/items", json={"group": "核心", "market": "us", "symbol": "AAPL", "name": "Apple"})
        assert item.status_code == 200
        watchlists = client.get("/api/watchlists")
        assert watchlists.status_code == 200
        assert "核心" in watchlists.json()["groups"]

        template = client.post(
            "/api/filter-templates",
            json={"name": "强势股", "market": "us", "conditions": [{"indicator": "macd", "period": 12, "operator": ">", "value": 0, "enabled": True}]},
        )
        assert template.status_code == 200
        template_id = template.json()["id"]
        updated = client.put(
            f"/api/filter-templates/{template_id}",
            json={"name": "强势股更新", "market": "us", "conditions": []},
        )
        assert updated.status_code == 200
        deleted = client.delete(f"/api/filter-templates/{template_id}")
        assert deleted.status_code == 200
        assert deleted.json()["deleted"] is True
