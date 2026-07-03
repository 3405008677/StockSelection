from __future__ import annotations

from uuid import uuid4

from .data_sources import fallback_daily, fetch_daily, fetch_intraday, fetch_universe
from .indicators import latest_indicators, ma, macd, rsi
from .models import FilterTemplate, FilterTemplateCreate, IndicatorCondition, Market, ScreenRequest, ScreenResponse, ScreenResult, StockDetail, WatchlistCreate, WatchlistItem, Watchlists
from .sample_data import CN_STOCKS, US_STOCKS
from .storage import daily_cache_path, intraday_cache_path, load_universe, read_candles, read_json, save_universe, user_file, write_candles, write_json


WATCHLISTS_FILE = "watchlists.json"
TEMPLATES_FILE = "filter_templates.json"


def merge_core_stocks(market: Market, stocks: list) -> list:
    core_stocks = CN_STOCKS if market == Market.cn else US_STOCKS
    merged = {stock.symbol: stock for stock in stocks}
    return [*core_stocks, *[stock for stock in stocks if stock.symbol not in {core.symbol for core in core_stocks}]] if merged else core_stocks


def get_universe(market: Market, refresh: bool = False) -> list:
    cached = load_universe(market)
    if cached and not refresh:
        return merge_core_stocks(market, cached)
    try:
        stocks = fetch_universe(market, limit=300 if market == Market.cn else None)
        if stocks:
            save_universe(market, stocks)
            return merge_core_stocks(market, stocks)
    except Exception:
        pass
    return merge_core_stocks(market, cached)


def get_daily_candles(market: Market, symbol: str, refresh: bool = False):
    path = daily_cache_path(market, symbol)
    cached = read_candles(path)
    if cached and not refresh:
        return cached, "cache", None
    if cached and not refresh:
        return cached, "cache", None
    try:
        candles = fetch_daily(market, symbol)
        write_candles(path, candles)
        return candles, "remote", None
    except Exception as exc:  # noqa: BLE001
        if cached:
            return cached, "cache", str(exc)
        candles = fallback_daily(market, symbol)
        write_candles(path, candles)
        return candles, "sample", str(exc)


def get_cached_or_sample_daily_candles(market: Market, symbol: str):
    path = daily_cache_path(market, symbol)
    cached = read_candles(path)
    if cached:
        return cached, "cache", None
    candles = fallback_daily(market, symbol)
    write_candles(path, candles)
    return candles, "sample", "无本地缓存，已使用样例数据"


def get_intraday_candles(market: Market, symbol: str, refresh: bool = False):
    path = intraday_cache_path(market, symbol)
    cached = read_candles(path)
    if cached and not refresh:
        return cached
    try:
        candles = fetch_intraday(market, symbol)
        write_candles(path, candles)
        return candles
    except Exception:
        return cached


def compare(left: float | None, operator: str, right: float) -> bool:
    if left is None:
        return False
    return {
        ">": left > right,
        ">=": left >= right,
        "<": left < right,
        "<=": left <= right,
    }[operator]


def condition_value(candles, condition: IndicatorCondition) -> float | None:
    if condition.indicator == "ma":
        return ma(candles, condition.period)
    if condition.indicator == "macd":
        return macd(candles)
    if condition.indicator == "rsi":
        return rsi(candles, condition.period)
    return None


def get_watchlists() -> Watchlists:
    return Watchlists.model_validate(read_json(user_file(WATCHLISTS_FILE), {"groups": {}}))


def save_watchlists(watchlists: Watchlists) -> None:
    write_json(user_file(WATCHLISTS_FILE), watchlists.model_dump(mode="json"))


def watchlist_symbols() -> set[tuple[Market, str]]:
    watchlists = get_watchlists()
    result: set[tuple[Market, str]] = set()
    for items in watchlists.groups.values():
        for item in items:
            result.add((item.market, item.symbol))
    return result


def add_watchlist_item(payload: WatchlistCreate) -> WatchlistItem:
    watchlists = get_watchlists()
    items = watchlists.groups.setdefault(payload.group, [])
    for item in items:
        if item.market == payload.market and item.symbol == payload.symbol:
            return item
    item = WatchlistItem(id=str(uuid4()), **payload.model_dump())
    items.append(item)
    save_watchlists(watchlists)
    return item


def delete_watchlist_item(item_id: str) -> bool:
    watchlists = get_watchlists()
    for group, items in watchlists.groups.items():
        remaining = [item for item in items if item.id != item_id]
        if len(remaining) != len(items):
            watchlists.groups[group] = remaining
            save_watchlists(watchlists)
            return True
    return False


def get_templates() -> list[FilterTemplate]:
    return [FilterTemplate.model_validate(row) for row in read_json(user_file(TEMPLATES_FILE), [])]


def save_templates(templates: list[FilterTemplate]) -> None:
    write_json(user_file(TEMPLATES_FILE), [template.model_dump(mode="json") for template in templates])


def create_template(payload: FilterTemplateCreate) -> FilterTemplate:
    templates = get_templates()
    template = FilterTemplate(id=str(uuid4()), **payload.model_dump())
    templates.append(template)
    save_templates(templates)
    return template


def update_template(template_id: str, payload: FilterTemplateCreate) -> FilterTemplate | None:
    templates = get_templates()
    for index, template in enumerate(templates):
        if template.id == template_id:
            updated = FilterTemplate(id=template_id, **payload.model_dump())
            templates[index] = updated
            save_templates(templates)
            return updated
    return None


def delete_template(template_id: str) -> bool:
    templates = get_templates()
    remaining = [template for template in templates if template.id != template_id]
    if len(remaining) == len(templates):
        return False
    save_templates(remaining)
    return True


def run_screen(request: ScreenRequest) -> ScreenResponse:
    stocks = get_universe(request.market)
    if request.symbols:
        symbols = set(request.symbols)
        stocks = [stock for stock in stocks if stock.symbol in symbols]
    watchlisted = watchlist_symbols()
    results: list[ScreenResult] = []
    errors: list[str] = []
    for stock in stocks:
        try:
            candles, source, source_error = get_cached_or_sample_daily_candles(stock.market, stock.symbol)
            if len(candles) < 2:
                errors.append(f"{stock.symbol} 日线数据不足")
                continue
            matched_reasons: list[str] = []
            passed = True
            for condition in request.conditions:
                if not condition.enabled:
                    continue
                value = condition_value(candles, condition)
                if not compare(value, condition.operator, condition.value):
                    passed = False
                    break
                matched_reasons.append(f"{condition.indicator.upper()}({condition.period}) {condition.operator} {condition.value}")
            if passed:
                latest = candles[-1]
                previous = candles[-2]
                change_percent = round((latest.close - previous.close) / previous.close * 100, 2)
                results.append(
                    ScreenResult(
                        symbol=stock.symbol,
                        name=stock.name,
                        market=stock.market,
                        latest_price=latest.close,
                        change_percent=change_percent,
                        volume=latest.volume,
                        matched_reasons=(matched_reasons or ["未启用筛选条件"]) + ([f"数据源: {source}"] if source != "remote" else []),
                        is_watchlisted=(stock.market, stock.symbol) in watchlisted,
                    )
                )
                if source_error:
                    errors.append(f"{stock.symbol} 远程数据失败，已使用 {source}: {source_error}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{stock.symbol}: {exc}")
    return ScreenResponse(results=results, failed_count=len(errors), errors=errors)


def get_stock_detail(market: Market, symbol: str) -> StockDetail | None:
    stocks = get_universe(market)
    stock = next((item for item in stocks if item.symbol == symbol), None)
    candles, _, _ = get_daily_candles(market, symbol)
    if stock is None or not candles:
        return None
    return StockDetail(stock=stock, latest=candles[-1], indicators=latest_indicators(candles), is_watchlisted=(market, symbol) in watchlist_symbols())


def get_intraday(market: Market, symbol: str):
    return get_intraday_candles(market, symbol)
