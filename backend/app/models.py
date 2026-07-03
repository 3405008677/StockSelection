from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Market(str, Enum):
    cn = "cn"
    us = "us"


class Stock(BaseModel):
    symbol: str
    name: str
    market: Market
    exchange: str


class Candle(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class IndicatorCondition(BaseModel):
    indicator: Literal["ma", "macd", "rsi"]
    period: int = Field(default=14, ge=1)
    operator: Literal[">", ">=", "<", "<="] = ">"
    value: float = 0
    enabled: bool = True


class ScreenRequest(BaseModel):
    market: Market
    symbols: list[str] | None = None
    conditions: list[IndicatorCondition] = Field(default_factory=list)


class ScreenResult(BaseModel):
    symbol: str
    name: str
    market: Market
    latest_price: float
    change_percent: float
    volume: int
    matched_reasons: list[str]
    is_watchlisted: bool


class ScreenResponse(BaseModel):
    results: list[ScreenResult]
    failed_count: int = 0
    errors: list[str] = Field(default_factory=list)


class WatchlistItem(BaseModel):
    id: str
    group: str
    market: Market
    symbol: str
    name: str


class Watchlists(BaseModel):
    groups: dict[str, list[WatchlistItem]] = Field(default_factory=dict)


class WatchlistCreate(BaseModel):
    group: str = "默认"
    market: Market
    symbol: str
    name: str


class FilterTemplate(BaseModel):
    id: str
    name: str
    market: Market
    conditions: list[IndicatorCondition]


class FilterTemplateCreate(BaseModel):
    name: str
    market: Market
    conditions: list[IndicatorCondition]


class StockDetail(BaseModel):
    stock: Stock
    latest: Candle
    indicators: dict[str, float | None]
    is_watchlisted: bool

