export type Market = 'cn' | 'us'

export interface Stock {
  symbol: string
  name: string
  market: Market
  exchange: string
}

export interface IndicatorCondition {
  indicator: 'ma' | 'macd' | 'rsi'
  period: number
  operator: '>' | '>=' | '<' | '<='
  value: number
  enabled: boolean
}

export interface ScreenResult {
  symbol: string
  name: string
  market: Market
  latest_price: number
  change_percent: number
  volume: number
  matched_reasons: string[]
  is_watchlisted: boolean
}

export interface WatchlistItem {
  id: string
  group: string
  market: Market
  symbol: string
  name: string
}

export interface Watchlists {
  groups: Record<string, WatchlistItem[]>
}

export interface FilterTemplate {
  id: string
  name: string
  market: Market
  conditions: IndicatorCondition[]
}

export interface Candle {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface StockDetail {
  stock: Stock
  latest: Candle
  indicators: Record<string, number | null>
  is_watchlisted: boolean
}

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...(options?.headers ?? {}) },
    ...options
  })
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `请求失败: ${response.status}`)
  }
  return response.json() as Promise<T>
}

export const api = {
  markets: () => request<Array<{ id: Market; name: string }>>('/api/markets'),
  universe: (market: Market) => request<Stock[]>(`/api/universe?market=${market}`),
  screen: (market: Market, conditions: IndicatorCondition[], symbols?: string[]) =>
    request<{ results: ScreenResult[]; failed_count: number; errors: string[] }>('/api/screen/run', {
      method: 'POST',
      body: JSON.stringify({ market, conditions, symbols })
    }),
  watchlists: () => request<Watchlists>('/api/watchlists'),
  addWatchlist: (item: { group: string; market: Market; symbol: string; name: string }) =>
    request<WatchlistItem>('/api/watchlists/items', { method: 'POST', body: JSON.stringify(item) }),
  deleteWatchlist: (id: string) => request<{ deleted: boolean }>(`/api/watchlists/items/${id}`, { method: 'DELETE' }),
  templates: () => request<FilterTemplate[]>('/api/filter-templates'),
  createTemplate: (template: { name: string; market: Market; conditions: IndicatorCondition[] }) =>
    request<FilterTemplate>('/api/filter-templates', { method: 'POST', body: JSON.stringify(template) }),
  updateTemplate: (id: string, template: { name: string; market: Market; conditions: IndicatorCondition[] }) =>
    request<FilterTemplate>(`/api/filter-templates/${id}`, { method: 'PUT', body: JSON.stringify(template) }),
  deleteTemplate: (id: string) => request<{ deleted: boolean }>(`/api/filter-templates/${id}`, { method: 'DELETE' }),
  detail: (market: Market, symbol: string) => request<StockDetail>(`/api/stocks/${market}/${symbol}`),
  intraday: (market: Market, symbol: string) => request<Candle[]>(`/api/stocks/${market}/${symbol}/intraday`)
}
