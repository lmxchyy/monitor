import hashlib
import re
import datetime as dt
from typing import Iterable


_COMPANY_SUFFIXES = [
    "有限责任公司",
    "股份有限公司",
    "有限公司",
    "集团有限公司",
    "集团",
    "公司",
]


def normalize_company_name(name: str) -> str:
    s = str(name).strip()
    s = s.replace("（", "(").replace("）", ")")
    s = s.replace(" ", "")
    return s


def guess_industry(name: str) -> str:
    mapping = {
        "银行": "金融服务",
        "证券": "金融服务",
        "信托": "金融服务",
        "保险": "金融服务",
        "基金": "金融服务",
        "科技": "信息技术",
        "软件": "信息技术",
        "互联网": "信息技术",
        "网络": "信息技术",
        "大数据": "信息技术",
        "人工智能": "信息技术",
        "工程": "建筑基建",
        "建筑": "建筑基建",
        "路桥": "建筑基建",
        "市政": "建筑基建",
        "房地": "建筑基建",
        "医药": "生物医药",
        "生物": "生物医药",
        "制药": "生物医药",
        "健康": "生物医药",
        "药业": "生物医药",
        "中粮": "消费零售",
        "商贸": "消费零售",
        "超市": "消费零售",
        "零售": "消费零售",
        "旅游": "消费零售",
        "餐饮": "消费零售",
        "大学": "教育科研",
        "学院": "教育科研",
        "研究所": "教育科研",
        "研究院": "教育科研",
        "小学": "教育科研",
        "中学": "教育科研",
        "能源": "电力能源",
        "石油": "电力能源",
        "石化": "电力能源",
        "电网": "电力能源",
        "电力": "电力能源",
        "燃气": "电力能源",
        "汽车": "汽车制造",
        "制造": "装备制造",
        "机械": "装备制造",
        "航天": "航空航天",
        "航空": "航空航天",
        "文化": "文化传媒",
        "传媒": "文化传媒",
        "广播": "文化传媒",
        "报社": "文化传媒",
        "视频": "文化传媒",
    }
    for key, industry in mapping.items():
        if key in name:
            return industry
    return "综合/其他"


def company_search_variants(name: str, aliases: str | None) -> list[str]:
    base = normalize_company_name(name)
    out: list[str] = [base]

    if aliases:
        for a in str(aliases).split("|"):
            a = normalize_company_name(a)
            if a and a not in out:
                out.append(a)

    for suf in _COMPANY_SUFFIXES:
        if base.endswith(suf):
            short = base[: -len(suf)]
            if short and short not in out:
                out.append(short)

    return out


def stable_fingerprint(parts: Iterable[str]) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(str(p).encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def extract_keywords(texts: list[str], max_keywords: int = 20) -> list[str]:
    # 简单v1：提取中英文数字的2-10长度token，统计频次。
    # 后续可替换为更好的分词/关键词算法。
    combined = "\n".join([t for t in texts if t])
    tokens = re.findall(r"[A-Za-z0-9_\-\.]{2,20}|[\u4e00-\u9fa5]{2,10}", combined)
    freq: dict[str, int] = {}
    for tok in tokens:
        freq[tok] = freq.get(tok, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    return [k for k, _ in ranked[:max_keywords]]


def extract_job_count(text: str) -> int:
    patterns = [
        r"共\s*(\d+)\s*个岗位",
        r"共\s*(\d+)\s*条结果",
        r"(\d+)\s*个在招岗位",
        r"Found\s*(\d+)\s*jobs",
        r"(\d+)\s*openings",
        r"(\d+)\s*positions",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return 0


def parse_funding_details(text: str) -> dict:
    # Round
    round_pattern = r"([A-Ga-g\+]\d*轮|种子轮|天使轮|Pre-A轮|Strategic|战略投资|IPO|定增|A\d?轮|B\d?轮|C\d?轮|D\d?轮|E\d?轮|F\d?轮|G\d?轮)"
    m_round = re.search(round_pattern, text)
    res_round = m_round.group(1) if m_round else None

    # Amount & Currency
    amount_pattern = r"(\d+\.?\d*|数)([万亿]?(?:元|美元|美金|港币|HKD|人民币))"
    m_amount = re.search(amount_pattern, text)
    res_amount = None
    res_currency = None
    if m_amount:
        res_amount = m_amount.group(1) + m_amount.group(2)
        unit = m_amount.group(2)
        if "美元" in unit or "美金" in unit or "USD" in unit:
            res_currency = "USD"
        elif "元" in unit or "人民币" in unit:
            res_currency = "CNY"
        elif "港币" in unit or "HKD" in unit:
            res_currency = "HKD"
        else:
            res_currency = unit

    # Investors
    investor_pattern = (
        r"(?:由|投资方为|投资方包括)\s*([^，。、]+?)(?:领投|投资|参投|跟投|等|$)"
    )
    m_investor = re.search(investor_pattern, text)
    res_investors = m_investor.group(1).strip() if m_investor else None

    return {
        "round": res_round,
        "amount": res_amount,
        "currency": res_currency,
        "investors": res_investors,
    }


def extract_event_date(text: str, default_date: dt.date | None = None) -> dt.date | None:
    # 1. 尝试匹配 YYYY年MM月DD日 或 YYYY-MM-DD
    m1 = re.search(r"(20\d{2})[年\-/](\d{1,2})[月\-/](\d{1,2})", text)
    if m1:
        try:
            return dt.date(int(m1.group(1)), int(m1.group(2)), int(m1.group(3)))
        except ValueError:
            pass

    # 2. 尝试匹配 YYYY年MM月
    m2 = re.search(r"(20\d{2})[年\-/](\d{1,2})月?", text)
    if m2:
        try:
            return dt.date(int(m2.group(1)), int(m2.group(2)), 1)
        except ValueError:
            pass

    # 3. 尝试匹配 MM月DD日 (补全今年)
    m3 = re.search(r"(\d{1,2})月(\d{1,2})日", text)
    if m3:
        try:
            year = default_date.year if default_date else dt.date.today().year
            return dt.date(year, int(m3.group(1)), int(m3.group(2)))
        except ValueError:
            pass

    # 4. 如果有 "近日", "日前", "刚刚", 则使用默认日期（发布日期）
    if any(kw in text for kw in ["近日", "日前", "刚刚", "今天", "本周"]):
        return default_date

    return default_date
