# StockSelection

本项目是一个本地 Web 量化选股工具 MVP，面向个人研究使用。后端使用 FastAPI，前端使用 Vue3 + Vite，数据和用户配置使用本地文件保存。

## 功能范围

- A 股和美股主流股票池样例
- A 股免费数据源：东方财富公开 HTTP 接口（A 股列表和日线）
- 美股免费数据源：yfinance（Yahoo Finance 日线和分钟）
- 远程数据失败时自动回退本地缓存/样例数据
- 日线技术指标筛选：MA、MACD、RSI
- 筛选结果表格、自选股管理、筛选模板管理
- 个股详情和少量分钟走势
- 本地 JSON/CSV 文件存储

## 后端启动

```powershell
Set-Location backend
uv run uvicorn app.main:app --reload
```

## 前端启动

```powershell
Set-Location frontend
npm install
npm run dev
```

## 验证命令

```powershell
uv run --project backend pytest
Set-Location frontend
npm run typecheck
npm run build
```

## 数据源说明

后端会优先尝试真实免费数据源：

- A 股股票池和日线：东方财富公开 HTTP 接口
- 美股日线/分钟：`yfinance.Ticker(...).history(...)`

如果免费数据源网络失败、限流或返回空数据，系统会继续使用本地缓存；没有缓存时使用样例数据，确保本地研究流程仍可运行。
