from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import httpx

from .models import Candle, Market, Stock
from .sample_data import CN_STOCKS, US_STOCKS, generate_daily, generate_intraday


def _float_value(value: Any) -> float:
    return round(float(value), 4)


def _int_value(value: Any) -> int:
    return int(float(value))


def fetch_cn_universe(limit: int | None = None) -> list[Stock]:
    response = httpx.get(
        "https://82.push2.eastmoney.com/api/qt/clist/get",
        params={
            "pn": 1,
            "pz": limit or 5000,
            "po": 1,
            "np": 1,
            "fltt": 2,
            "invt": 2,
            "fid": "f3",
            "fs": "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81",
            "fields": "f12,f13,f14",
        },
        timeout=15,
    )
    response.raise_for_status()
    rows = response.json().get("data", {}).get("diff", []) or []
    stocks = [Stock(symbol=str(row["f12"]), name=str(row["f14"]), market=Market.cn, exchange="SH" if str(row.get("f13")) == "1" else "SZ") for row in rows]
    return stocks[:limit] if limit else stocks


def fetch_us_universe() -> list[Stock]:
    return US_STOCKS


def fetch_universe(market: Market, limit: int | None = None) -> list[Stock]:
    if market == Market.cn:
        return fetch_cn_universe(limit=limit)
    return fetch_us_universe()


def fetch_cn_daily(symbol: str, days: int = 90) -> list[Candle]:
    end = date.today()
    start = end - timedelta(days=days * 2)
    secid = f"1.{symbol}" if symbol.startswith("6") else f"0.{symbol}"
    params = {
        "secid": secid,
        "klt": 101,
        "fqt": 0,
        "beg": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
    }
    last_error: Exception | None = None
    rows = []
    for host in ["https://push2his.eastmoney.com", "https://push2his.eastmoney.com", "http://push2his.eastmoney.com"]:
        try:
            response = httpx.get(f"{host}/api/qt/stock/kline/get", params=params, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            rows = response.json().get("data", {}).get("klines", []) or []
            if rows:
                break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    if not rows:
        yahoo_symbol = f"{symbol}.SS" if symbol.startswith("6") else f"{symbol}.SZ"
        try:
            return fetch_us_history(yahoo_symbol, period="3mo", interval="1d")[-days:]
        except Exception as exc:  # noqa: BLE001
            if last_error:
                raise last_error from exc
            raise
    candles = []
    for row in rows[-days:]:
        fields = row.split(",")
        candles.append(Candle(date=fields[0], open=_float_value(fields[1]), close=_float_value(fields[2]), high=_float_value(fields[3]), low=_float_value(fields[4]), volume=_int_value(fields[5])))
    if not candles:
        raise ValueError(f"AkShare 未返回 {symbol} 日线数据")
    return candles


def fetch_us_history(symbol: str, period: str, interval: str) -> list[Candle]:
    import yfinance as yf

    frame = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=False, raise_errors=True)
    candles = [
        Candle(
            date=index.strftime("%Y-%m-%d %H:%M") if interval != "1d" else index.strftime("%Y-%m-%d"),
            open=_float_value(row["Open"]),
            high=_float_value(row["High"]),
            low=_float_value(row["Low"]),
            close=_float_value(row["Close"]),
            volume=_int_value(row["Volume"]),
        )
        for index, row in frame.iterrows()
    ]
    if not candles:
        raise ValueError(f"yfinance 未返回 {symbol} {interval} 数据")
    return candles


def fetch_daily(market: Market, symbol: str, days: int = 90) -> list[Candle]:
    if market == Market.cn:
        return fetch_cn_daily(symbol, days=days)
    return fetch_us_history(symbol, period="3mo", interval="1d")[-days:]


def fetch_intraday(market: Market, symbol: str) -> list[Candle]:
    if market == Market.us:
        return fetch_us_history(symbol, period="1d", interval="5m")
    sample = next((stock for stock in CN_STOCKS if stock.symbol == symbol), None)
    seed = 100.0 if sample is None else {"600519": 1680, "000001": 11, "300750": 210}.get(symbol, 100.0)
    return generate_intraday(seed)


def fallback_daily(market: Market, symbol: str) -> list[Candle]:
    seeds = {
        "600519": (1680, 2.6),
        "000001": (11, 0.05),
        "300750": (210, 0.8),
        "AAPL": (190, 0.45),
        "MSFT": (420, 0.7),
        "NVDA": (125, 0.9),
    }
    seed_price, trend = seeds.get(symbol, (100.0, 0.2))
    return generate_daily(seed_price, trend)
