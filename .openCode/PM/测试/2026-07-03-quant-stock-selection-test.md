# 量化选股工具 MVP 测试记录

## 测试时间

2026-07-03 16:00:42

## 执行命令与结果

- `uv run --project "backend" pytest`
  - 结果：通过，3 passed。
  - 备注：存在 FastAPI/Starlette deprecation warnings，不影响当前功能。

- `npm install`
  - 首次结果：失败，npm registry 响应体大小不一致 `EBADSIZE`。
  - 修复动作：执行 `npm cache verify` 后重试。
  - 最终结果：通过，依赖安装成功，0 vulnerabilities。

- `npm run typecheck`
  - 首次结果：失败。
  - 失败原因：`WatchlistItem` 类型不能传入详情方法；缺少 CSS side-effect import 类型声明。
  - 修复动作：扩展 `openDetail` 参数类型，新增 `frontend/src/vite-env.d.ts`。
  - 最终结果：通过。

- `npm run build`
  - 首次结果：失败，原因同 typecheck。
  - 修复后结果：通过，Vite build 成功。

- 接口 smoke：`uv run --project "backend" python -c ... POST /api/screen/run ...`
  - 首次结果：失败，原因是根目录执行缺少 `PYTHONPATH=backend`。
  - 修复动作：使用 `$env:PYTHONPATH="backend"`。
  - 最终结果：通过，返回 HTTP 200，筛选结果数量为 3。

- 浏览器 smoke：Playwright 打开 `http://127.0.0.1:5173`
  - 验证内容：页面加载、执行筛选、加入自选、保存模板、打开详情、查看分钟走势。
  - 首次发现问题：分钟样例数据出现 `09:60/09:65` 非法时间。
  - 修复动作：将分钟数据生成逻辑改为基于 `datetime + timedelta(minutes=5)`，并每次启动刷新分钟缓存。
  - 最终结果：通过。页面展示 `09:30` 到 `10:05`，控制台无错误。

## 验证结论

通过。

## 剩余风险

- 当前使用样例数据和可替换数据源接口，尚未接入真实免费公开行情源。
- 当前目录不是 Git 仓库，无法完成自动提交。
- 后端存在 `on_event` deprecation warning，后续可迁移到 FastAPI lifespan。
