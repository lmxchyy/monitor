from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

import pymysql
from jinja2 import Template


HTML_TEMPLATE = Template(
    """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>monitor results {{ date }}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body { font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,"Noto Sans","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif; margin: 24px; color: #111; background: #f3f4f6; }
    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 32px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    h1 { font-size: 24px; margin: 0 0 12px; color: #1f2937; border-left: 4px solid #3b82f6; padding-left: 12px; }
    h2 { font-size: 18px; margin: 32px 0 12px; color: #374151; border-bottom: 1px solid #e5e7eb; padding-bottom: 8px; }
    .meta { color: #6b7280; font-size: 13px; margin-bottom: 24px; }
    .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 24px; margin-bottom: 32px; }
    .chart-card { background: #f9fafb; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb; }
    table { border-collapse: collapse; width: 100%; margin: 8px 0 16px; background: white; }
    th, td { border: 1px solid #e5e7eb; padding: 10px 12px; font-size: 13px; vertical-align: top; }
    th { background: #f9fafb; text-align: left; color: #4b5563; font-weight: 600; }
    tr:hover { background: #f1f5f9; }
    .hint { color: #9ca3af; font-size: 12px; margin-top: -8px; margin-bottom: 16px; }
    .tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 500; }
    .tag-blue { background: #dbeafe; color: #1e40af; }
  </style>
</head>
<body>
  <div class="container">
    <h1>企业监控驾驶舱</h1>
    <div class="meta">报告生成：{{ generated_at }} | 统计日期：{{ date }} | 监控规模：{{ company_count }}家</div>

    <div class="dashboard">
      <div class="chart-card">
        <h3>行业人才需求分布</h3>
        <canvas id="industryHiringChart"></canvas>
      </div>
      <div class="chart-card">
        <h3>最具活力企业 TOP 10 (招聘)</h3>
        <canvas id="topHiringChart"></canvas>
      </div>
    </div>

    <h2>最新融资事件明细</h2>
    {{ tables.funding_details }}

    <h2>每日核心指标</h2>
    {{ tables.metrics }}

    <h2>数据同步状态</h2>
    <div style="display: flex; gap: 20px;">
      <div style="flex: 1;"><h3>招聘同步 (按渠道)</h3>{{ tables.hiring_counts }}</div>
      <div style="flex: 1;"><h3>融资同步 (按来源)</h3>{{ tables.funding_counts }}</div>
    </div>
  </div>

  <script>
    const industryData = {{ chart_data.industry_hiring | safe }};
    new Chart(document.getElementById('industryHiringChart'), {
      type: 'doughnut',
      data: {
        labels: industryData.labels,
        datasets: [{
          data: industryData.values,
          backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#6b7280', '#ec4899', '#06b6d4']
        }]
      },
      options: { plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } } } }
    });

    const topHiringData = {{ chart_data.top_hiring | safe }};
    new Chart(document.getElementById('topHiringChart'), {
      type: 'bar',
      data: {
        labels: topHiringData.labels,
        datasets: [{
          label: '在招岗位数',
          data: topHiringData.values,
          backgroundColor: '#3b82f6'
        }]
      },
      options: { 
        indexAxis: 'y',
        plugins: { legend: { display: false } },
        scales: { x: { grid: { display: false } }, y: { grid: { display: false } } }
      }
    });
  </script>
</body>
</html>
"""
)


COL_LABELS = {
    "id": "公司ID",
    "name": "公司名称",
    "aliases": "别名/配置",
    "snapshot_date": "日期",
    "channel": "渠道",
    "cnt": "记录数",
    "source_type": "来源类型",
    "source_name": "来源",
    "date": "日期",
    "open_jobs_total": "在招岗位数",
    "funding_last_90d_count": "近90天融资次数",
    "latest_funding_date": "最新融资日期",
    "event_date": "融资日期",
    "round": "融资轮次",
    "amount": "融资金额",
    "currency": "币种",
    "investors": "投资方/来源",
    "source_url": "来源链接",
    "confidence": "置信度",
}

CHANNEL_LABELS = {
    "company_website": "官网",
    "boss": "BOSS直聘",
    "zhilian": "智联招聘",
    "51job": "前程无忧",
}

SOURCE_TYPE_LABELS = {
    "news_placeholder": "媒体新闻",
    "disclosure_placeholder": "官方披露",
    "rss_candidate": "RSS实时频道",
    "web_list": "网页列表",
}


def db_cfg() -> dict:
    return {
        "host": os.getenv("MONITOR_DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("MONITOR_DB_PORT", "3306")),
        "user": os.getenv("MONITOR_DB_USER", "monitor"),
        "password": os.getenv("MONITOR_DB_PASSWORD", "monitor"),
        "db": os.getenv("MONITOR_DB_NAME", "monitor"),
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
    }


def query(sql: str) -> list[dict]:
    cfg = db_cfg()
    conn = pymysql.connect(**cfg)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return list(cur.fetchall())
    finally:
        conn.close()


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def map_cell(col: str, val) -> str:
    if val is None:
        return ""
    s = str(val)
    if col == "channel":
        s = CHANNEL_LABELS.get(s, s)
    elif col == "source_type":
        s = SOURCE_TYPE_LABELS.get(s, s)
    elif col == "source_url":
        safe = esc(s)
        return f'<a href="{safe}" target="_blank" rel="noopener noreferrer">查看原文</a>'
    elif col == "confidence":
        try:
            return f"{float(s):.2f}"
        except ValueError:
            pass
    return esc(s)


def to_table(rows: list[dict]) -> str:
    if not rows:
        return '<div class="meta">(no rows)</div>'

    cols = list(rows[0].keys())
    head = "".join([f"<th>{esc(COL_LABELS.get(c, c))}</th>" for c in cols])

    parts = ["<table>"]
    parts.append(f"<thead><tr>{head}</tr></thead>")
    parts.append("<tbody>")
    for r in rows:
        tds = "".join([f"<td>{map_cell(c, r.get(c))}</td>" for c in cols])
        parts.append(f"<tr>{tds}</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def main() -> None:
    today = dt.date.today().isoformat()
    out_dir = Path(__file__).resolve().parents[0] / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"results_{today}.html"

    # 1. 基础数据查询
    # (companies 暂时不需要全量展示，节省页面空间)
    company_count_rows = query("SELECT COUNT(*) AS cnt FROM companies")
    company_count = int(company_count_rows[0]["cnt"]) if company_count_rows else 0
    
    hiring_counts = query(
        "SELECT snapshot_date, channel, COUNT(*) cnt FROM hiring_snapshots GROUP BY snapshot_date, channel ORDER BY snapshot_date DESC, channel"
    )
    funding_counts = query(
        "SELECT source_type, ROUND(AVG(confidence), 3) confidence, COUNT(*) cnt "
        "FROM funding_events GROUP BY source_type ORDER BY cnt DESC, source_type"
    )
    funding_details = query(
        "SELECT f.event_date, c.name, f.round, f.amount, f.currency, f.investors, "
        "CASE WHEN JSON_VALID(f.raw_text) THEN "
        "COALESCE(JSON_UNQUOTE(JSON_EXTRACT(f.raw_text, '$.source')), JSON_UNQUOTE(JSON_EXTRACT(f.raw_text, '$.feed')), f.source_type) "
        "ELSE f.source_type END AS source_name, "
        "f.confidence, f.source_url "
        "FROM funding_events f JOIN companies c ON c.id=f.company_id "
        "WHERE f.source_type='rss_candidate' OR f.source_type='web_list' OR f.amount IS NOT NULL "
        "ORDER BY f.event_date DESC, f.confidence DESC LIMIT 50"
    )
    metrics = query(
        "SELECT m.date, c.name, c.industry, m.open_jobs_total, m.funding_last_90d_count, m.latest_funding_date "
        "FROM company_daily_metrics m JOIN companies c ON c.id=m.company_id "
        "WHERE m.date = (SELECT MAX(date) FROM company_daily_metrics) "
        "ORDER BY m.open_jobs_total DESC, c.id LIMIT 100"
    )

    # 2. 图表数据计算
    # 行业招聘分布
    industry_hiring = query(
        "SELECT c.industry, SUM(m.open_jobs_total) as val "
        "FROM company_daily_metrics m JOIN companies c ON c.id=m.company_id "
        "WHERE m.date = (SELECT MAX(date) FROM company_daily_metrics) "
        "GROUP BY c.industry ORDER BY val DESC"
    )
    chart_industry = {
        "labels": [r["industry"] for r in industry_hiring],
        "values": [int(r["val"]) for r in industry_hiring]
    }

    # 招聘 TOP 10 企业
    top_hiring = query(
        "SELECT c.name, m.open_jobs_total as val "
        "FROM company_daily_metrics m JOIN companies c ON c.id=m.company_id "
        "WHERE m.date = (SELECT MAX(date) FROM company_daily_metrics) "
        "ORDER BY val DESC LIMIT 10"
    )
    chart_top_hiring = {
        "labels": [r["name"] for r in top_hiring][::-1], # 翻转以便条形图从大到小排列
        "values": [int(r["val"]) for r in top_hiring][::-1]
    }

    # 3. 渲染
    import json
    html = HTML_TEMPLATE.render(
        date=today,
        generated_at=dt.datetime.now().isoformat(timespec="seconds"),
        company_count=company_count,
        tables={
            "hiring_counts": to_table(hiring_counts),
            "funding_counts": to_table(funding_counts),
            "funding_details": to_table(funding_details),
            "metrics": to_table(metrics),
        },
        chart_data={
            "industry_hiring": json.dumps(chart_industry),
            "top_hiring": json.dumps(chart_top_hiring)
        }
    )

    out_path.write_text(html, encoding="utf-8")
    print(str(out_path))


if __name__ == "__main__":
    main()
