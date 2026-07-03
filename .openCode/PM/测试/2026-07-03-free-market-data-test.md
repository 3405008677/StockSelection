# 免费行情数据源接入测试记录

## 测试时间

2026-07-03 16:34:55

## 变更范围

- 新增 `backend/app/data_sources.py`。
- A 股接入东方财富公开 HTTP 接口，失败时回退 Yahoo Finance A 股后缀代码（`.SZ`/`.SS`）。
- 美股接入 `yfinance`。
- 筛选交互路径优先使用缓存/样例，避免点击筛选时被免费远程接口阻塞。
- 显式刷新路径可验证真实免费远程数据。
- 前端 API 改为直连 `http://127.0.0.1:8000`，避免 Vite 代理旧连接卡住。

## 执行命令与结果

- `uv run --project "backend" pytest`
  - 结果：通过，3 passed。

- `npm run typecheck`
  - 结果：通过。

- `npm run build`
  - 结果：通过。

- A 股真实源 smoke：`get_daily_candles(Market.cn, '000001', refresh=True)`
  - 结果：通过，`source=remote`，返回 61 条日线。
  - 备注：东方财富日线接口一度返回 502，已增加 Yahoo Finance A 股后缀备用源。

- 美股真实源 smoke：`get_daily_candles(Market.us, 'AAPL', refresh=True)`
  - 结果：通过，`source=remote`，返回 62 条日线。

- 筛选接口 smoke：核心 A 股代码 `000001/600519/300750`
  - 结果：通过，返回 3 条结果，失败数 0。

- 浏览器 smoke：Playwright 打开 `http://127.0.0.1:5173`
  - 结果：通过。
  - 验证内容：执行筛选返回 2 行结果；打开详情成功；页面包含“分钟走势”。

## 失败与修复

- `akshare` 依赖安装失败：传递依赖 `jsonpath==0.82.2` 在当前环境构建失败。
- 修复：移除 AkShare 依赖，改为直接调用东方财富公开 HTTP 接口，并保留 yfinance。
- 浏览器筛选曾卡住：原因是空股票池时前端发送 `symbols: []`，后端按全市场扫描并触发大量请求。
- 修复：前端无股票池时使用核心默认代码；后端筛选交互路径只使用缓存/样例，远程刷新改为显式路径。

## 验证结论

通过。

## 剩余风险

- 免费公开接口存在限流、502、断连、字段变化风险。
- A 股东方财富接口失败时会回退 Yahoo Finance 后缀源；如果两者都失败，将使用本地缓存/样例。
- 当前尚未做后台全量缓存任务，页面默认只扫描核心股票，避免交互卡顿。
