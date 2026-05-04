# monitor（企业融资 & 招聘监控系统）

## 目标
- **监控规模**：当前已导入 **500 家** 北京重点企业名单，长期目标 5000 家。
- **每日跑批**：
  - **融资**：已接入 **IT 桔子**、**投资界**、**36氪**、**创业邦** 等核心源，支持金额、轮次、投资方及真实发生日期的语义解析。
  - **招聘**：支持“企业官网”动态抓取（集成 Playwright）及主流招聘站点（BOSS、智联等）的行业化模拟分析。
- **数据分析**：MySQL（Docker）落库，内置自动指标计算与 Chart.js 可视化驾驶舱。

## 核心进展：从“占位”到“实战”
系统已完成从 MVP 到专业版的关键进化：
1. **动态渲染**：集成 Playwright，攻克 SPA 单页应用及高防御站点（如 IT 桔子）的采集难题。
2. **深度解析**：新增语义提取模块，自动从新闻正文中识别融资额、投资方及实际日期。
3. **行业画像**：全量 500 家公司已完成行业打标，支持按行业维度的需求热度分析。
4. **决策看板**：HTML 报告升级为“监控驾驶舱”，包含行业分布图、招聘 Top 榜及融资明细。

## 目录结构
- `docker/`：MySQL 容器与初始化脚本
- `etl/`：ETL 脚本（Python）
- `data/`：输入数据（公司名单 CSV）
- `results/`：可视化输出结果（HTML 看板）

## 快速开始 (Windows/PowerShell)
### 一键全跑
会自动启动数据库、安装依赖、同步 500 家企业动态并生成可视化看板。
```powershell
.\run_all.ps1
```

### 生成可视化报告
```powershell
.\show_results.ps1
```

### 本地实时看板
启动一个 Vue 本地 Web 看板，后台每 10 分钟自动跑一次 ETL，页面每 60 秒自动刷新报告：
```powershell
python monitor_web.py --host 127.0.0.1 --port 8000 --interval 600
```

访问：
```text
http://127.0.0.1:8000
```

## 数据源配置
在 `etl/config/sources.yml` 中管理：
- `rss_feeds`: 媒体订阅源。
- `disclosure_lists`: IT 桔子等网页列表源，支持 `fetcher`、`selectors` 和 `capture_api`：
  - `fetcher`: `get` / `auto` / `dynamic` / `stealth`，默认会对 IT 桔子使用 `stealth`。
  - `selectors`: 用 CSS 选择器指定列表块，减少全页误匹配。
  - `capture_api`: 动态渲染时记录 XHR/fetch 请求，便于定位真实数据接口。

调试动态页面 API：
```powershell
python etl\inspect_page_apis.py https://www.itjuzi.com/investevents --fetcher stealth
```

## 仪表盘
- **HTML 报告**：位于 `results/results_YYYY-MM-DD.html`。
- **重点表**：
  - `funding_events`: 结构化融资事件。
  - `company_daily_metrics`: 每日运行指标（已激活真实计算逻辑）。
