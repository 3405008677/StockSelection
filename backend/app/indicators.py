from __future__ import annotations

from .models import Candle


def closes(candles: list[Candle]) -> list[float]:
    return [candle.close for candle in candles]


def ma(candles: list[Candle], period: int) -> float | None:
    values = closes(candles)
    if len(values) < period:
        return None
    return round(sum(values[-period:]) / period, 4)


def ema(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    multiplier = 2 / (period + 1)
    result = [values[0]]
    for value in values[1:]:
        result.append((value - result[-1]) * multiplier + result[-1])
    return result


def macd(candles: list[Candle]) -> float | None:
    values = closes(candles)
    if len(values) < 26:
        return None
    ema12 = ema(values, 12)
    ema26 = ema(values, 26)
    diff = [short - long for short, long in zip(ema12, ema26)]
    dea = ema(diff, 9)
    return round((diff[-1] - dea[-1]) * 2, 4)


def rsi(candles: list[Candle], period: int = 14) -> float | None:
    values = closes(candles)
    if len(values) <= period:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for current, previous in zip(values[-period:], values[-period - 1 : -1]):
        change = current - previous
        gains.append(max(change, 0))
        losses.append(abs(min(change, 0)))
    average_gain = sum(gains) / period
    average_loss = sum(losses) / period
    if average_loss == 0:
        return 100.0
    return round(100 - 100 / (1 + average_gain / average_loss), 4)


def latest_indicators(candles: list[Candle]) -> dict[str, float | None]:
    return {
        "ma5": ma(candles, 5),
        "ma20": ma(candles, 20),
        "macd": macd(candles),
        "rsi14": rsi(candles, 14),
    }
