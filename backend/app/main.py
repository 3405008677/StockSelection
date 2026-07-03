from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import FilterTemplate, FilterTemplateCreate, Market, ScreenRequest, ScreenResponse, Stock, StockDetail, WatchlistCreate, WatchlistItem, Watchlists
from .sample_data import ensure_sample_data
from .services import add_watchlist_item, create_template, delete_template, delete_watchlist_item, get_intraday, get_stock_detail, get_templates, get_universe, get_watchlists, run_screen, update_template
from .storage import ensure_data_dirs


app = FastAPI(title="StockSelection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    ensure_data_dirs()
    ensure_sample_data()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/markets")
def markets() -> list[dict[str, str]]:
    return [{"id": "cn", "name": "A 股"}, {"id": "us", "name": "美股"}]


@app.get("/api/universe", response_model=list[Stock])
def universe(market: Market) -> list[Stock]:
    return get_universe(market)


@app.post("/api/screen/run", response_model=ScreenResponse)
def screen(request: ScreenRequest) -> ScreenResponse:
    return run_screen(request)


@app.get("/api/stocks/{market}/{symbol}", response_model=StockDetail)
def stock_detail(market: Market, symbol: str) -> StockDetail:
    detail = get_stock_detail(market, symbol)
    if detail is None:
        raise HTTPException(status_code=404, detail="股票详情不存在")
    return detail


@app.get("/api/stocks/{market}/{symbol}/intraday")
def stock_intraday(market: Market, symbol: str):
    return get_intraday(market, symbol)


@app.get("/api/watchlists", response_model=Watchlists)
def watchlists() -> Watchlists:
    return get_watchlists()


@app.post("/api/watchlists/items", response_model=WatchlistItem)
def add_watchlist(payload: WatchlistCreate) -> WatchlistItem:
    return add_watchlist_item(payload)


@app.delete("/api/watchlists/items/{item_id}")
def remove_watchlist(item_id: str) -> dict[str, bool]:
    return {"deleted": delete_watchlist_item(item_id)}


@app.get("/api/filter-templates", response_model=list[FilterTemplate])
def filter_templates() -> list[FilterTemplate]:
    return get_templates()


@app.post("/api/filter-templates", response_model=FilterTemplate)
def add_template(payload: FilterTemplateCreate) -> FilterTemplate:
    return create_template(payload)


@app.put("/api/filter-templates/{template_id}", response_model=FilterTemplate)
def edit_template(template_id: str, payload: FilterTemplateCreate) -> FilterTemplate:
    template = update_template(template_id, payload)
    if template is None:
        raise HTTPException(status_code=404, detail="筛选模板不存在")
    return template


@app.delete("/api/filter-templates/{template_id}")
def remove_template(template_id: str) -> dict[str, bool]:
    return {"deleted": delete_template(template_id)}
