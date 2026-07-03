from __future__ import annotations

from datetime import date, datetime, timedelta

from .models import Candle, Market, Stock
from .storage import daily_cache_path, intraday_cache_path, read_candles, universe_path, write_candles, write_json


CN_STOCKS = [
    Stock(symbol="600519", name="贵州茅台", market=Market.cn, exchange="SH"),
    Stock(symbol="000001", name="平安银行", market=Market.cn, exchange="SZ"),
    Stock(symbol="300750", name="宁德时代", market=Market.cn, exchange="SZ"),
]

US_STOCKS = [
    Stock(symbol="AAPL", name="Apple", market=Market.us, exchange="NASDAQ"),
    Stock(symbol="MSFT", name="Microsoft", market=Market.us, exchange="NASDAQ"),
    Stock(symbol="NVDA", name="NVIDIA", market=Market.us, exchange="NASDAQ"),
]


def generate_daily(seed_price: float, trend: float) -> list[Candle]:
    start = date.today() - timedelta(days=80)
    candles: list[Candle] = []
    price = seed_price
    for index in range(60):
        current = start + timedelta(days=index)
        price = max(1, price + trend + ((index % 7) - 3) * 0.18)
        close = round(price, 2)
        candles.append(
            Candle(
                date=current.isoformat(),
                open=round(close * 0.99, 2),
                high=round(close * 1.02, 2),
                low=round(close * 0.98, 2),
                close=close,
                volume=1_000_000 + index * 15_000,
            )
        )
    return candles


def generate_intraday(seed_price: float) -> list[Candle]:
    start = datetime.combine(date.today(), datetime.strptime("09:30", "%H:%M").time())
    return [
        Candle(date=(start + timedelta(minutes=index * 5)).strftime("%Y-%m-%d %H:%M"), open=seed_price + index * 0.1, high=seed_price + index * 0.15, low=seed_price, close=seed_price + index * 0.12, volume=10000 + index * 800)
        for index in range(8)
    ]


def ensure_sample_data() -> None:
    write_json(universe_path(Market.cn), [stock.model_dump(mode="json") for stock in CN_STOCKS])
    write_json(universe_path(Market.us), [stock.model_dump(mode="json") for stock in US_STOCKS])
    seeds = {
        "600519": (1680, 2.6),
        "000001": (11, 0.05),
        "300750": (210, 0.8),
        "AAPL": (190, 0.45),
        "MSFT": (420, 0.7),
        "NVDA": (125, 0.9),
    }
    for stock in [*CN_STOCKS, *US_STOCKS]:
        seed_price, trend = seeds[stock.symbol]
        daily_path = daily_cache_path(stock.market, stock.symbol)
        intraday_path = intraday_cache_path(stock.market, stock.symbol)
        if not read_candles(daily_path):
            write_candles(daily_path, generate_daily(seed_price, trend))
        write_candles(intraday_path, generate_intraday(seed_price))
