from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .models import Candle, Market, Stock


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT.parent / "data"


def ensure_data_dirs() -> None:
    for relative_path in [
        "universe",
        "cache/daily/cn",
        "cache/daily/us",
        "cache/intraday/cn",
        "cache/intraday/us",
        "user",
        "logs",
    ]:
        (DATA_DIR / relative_path).mkdir(parents=True, exist_ok=True)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 文件格式错误: {path}") from exc


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def universe_path(market: Market) -> Path:
    return DATA_DIR / "universe" / ("cn_stocks.json" if market == Market.cn else "us_popular_stocks.json")


def load_universe(market: Market) -> list[Stock]:
    rows = read_json(universe_path(market), [])
    return [Stock.model_validate(row) for row in rows]


def save_universe(market: Market, stocks: list[Stock]) -> None:
    write_json(universe_path(market), [stock.model_dump(mode="json") for stock in stocks])


def daily_cache_path(market: Market, symbol: str) -> Path:
    return DATA_DIR / "cache" / "daily" / market.value / f"{symbol}.csv"


def intraday_cache_path(market: Market, symbol: str) -> Path:
    return DATA_DIR / "cache" / "intraday" / market.value / f"{symbol}.csv"


def read_candles(path: Path) -> list[Candle]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as file:
        rows = csv.DictReader(file)
        return [
            Candle(
                date=str(row["date"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=int(float(row["volume"])),
            )
            for row in rows
        ]


def write_candles(path: Path, candles: list[Candle]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["date", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        for candle in candles:
            writer.writerow(candle.model_dump())


def user_file(name: str) -> Path:
    return DATA_DIR / "user" / name
