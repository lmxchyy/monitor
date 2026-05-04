from __future__ import annotations

import datetime as dt
from urllib.parse import quote

from sources.base import HiringSource, json_dumps_compact
from sources.http import fetch_html, parse_int_loose, to_soup
from sources.types import HiringSnapshot


import random

def _guess_industry_keywords(company_name: str) -> list[str]:
    # 根据名称简单猜测行业并返回关键词
    mapping = {
        "银行": ["客户经理", "风控专员", "柜员", "审计", "金融科技"],
        "证券": ["分析师", "投顾", "合规", "交易员", "IT开发"],
        "保险": ["理赔", "精算", "电销", "渠道经理"],
        "科技": ["架构师", "前端开发", "后端", "产品经理", "测试"],
        "工程": ["项目经理", "安全员", "造价师", "施工员"],
        "医院": ["医师", "护士", "药剂师", "化验员"],
        "学校": ["教师", "辅导员", "教务", "行政"],
        "商贸": ["采购", "店长", "理货员", "物流主管"],
        "文化": ["文案", "策划", "新媒体运营", "设计师"],
        "制造": ["机械工程师", "质检", "车间主任", "工艺师"],
    }
    for key, words in mapping.items():
        if key in company_name:
            return words
    return ["销售", "行政", "财务", "人事", "市场专员"]

class BossZhipinSource(HiringSource):
    channel = "boss"

    def fetch(self, company: dict, run_date: dt.date) -> HiringSnapshot | None:
        q = quote(company["name"])
        url = f"https://www.zhipin.com/web/geek/job?query={q}&city=101010100"
        
        random.seed(int(company["id"]) + int(run_date.strftime("%Y%m%d")))
        simulated_count = random.randint(10, 50)
        keywords = _guess_industry_keywords(company["name"])
        
        raw = {"status": "simulated", "reason": "no-auth", "suggested_url": url, "simulated": True}
        return HiringSnapshot(
            company_id=int(company["id"]),
            snapshot_date=run_date,
            channel=self.channel,
            open_jobs_count=simulated_count,
            categories=[],
            keywords=keywords,
            source_url=url,
            raw_payload=json_dumps_compact(raw),
            confidence=0.100,
        )


class ZhilianSource(HiringSource):
    channel = "zhilian"

    def fetch(self, company: dict, run_date: dt.date) -> HiringSnapshot | None:
        q = quote(company["name"])
        url = f"https://sou.zhaopin.com/?jl=530&kw={q}"
        
        random.seed(int(company["id"]) + int(run_date.strftime("%Y%m%d")) + 1)
        simulated_count = random.randint(5, 40)
        keywords = _guess_industry_keywords(company["name"])
        
        raw = {"status": "simulated", "reason": "no-auth", "suggested_url": url, "simulated": True}
        return HiringSnapshot(
            company_id=int(company["id"]),
            snapshot_date=run_date,
            channel=self.channel,
            open_jobs_count=simulated_count,
            categories=[],
            keywords=keywords,
            source_url=url,
            raw_payload=json_dumps_compact(raw),
            confidence=0.100,
        )


class _Placeholder51JobSource(HiringSource):
    channel = "51job"

    def fetch(self, company: dict, run_date: dt.date) -> HiringSnapshot | None:
        q = quote(company["name"])
        url = f"https://search.51job.com/list/030000,000000,0000,00,9,99,{q},2,1.html"
        
        random.seed(int(company["id"]) + int(run_date.strftime("%Y%m%d")) + 2)
        simulated_count = random.randint(8, 60)
        keywords = _guess_industry_keywords(company["name"])
        
        raw = {"status": "simulated", "reason": "no-auth", "suggested_url": url, "simulated": True}
        return HiringSnapshot(
            company_id=int(company["id"]),
            snapshot_date=run_date,
            channel=self.channel,
            open_jobs_count=simulated_count,
            categories=[],
            keywords=keywords,
            source_url=url,
            raw_payload=json_dumps_compact(raw),
            confidence=0.100,
        )
