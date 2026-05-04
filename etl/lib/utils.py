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
    if res_investors:
        res_investors = re.sub(r"(?:参与|联合|共同|独家|持续|继续|战略)$", "", res_investors).strip()

    return {
        "round": res_round,
        "amount": res_amount,
        "currency": res_currency,
        "investors": res_investors,
    }


_FUNDING_SIGNAL_PATTERNS = [
    r"融资",
    r"融得",
    r"完成.{0,12}(?:轮|融资|投资)",
    r"获得.{0,12}(?:融资|投资|注资)",
    r"获.{0,12}(?:融资|投资|注资)",
    r"领投",
    r"参投",
    r"跟投",
    r"独家投资",
    r"战略投资",
    r"增资",
    r"定增",
    r"募资",
    r"并购",
    r"收购",
    r"IPO",
    r"上市",
    r"(?:种子|天使|Pre-A|Pre-B|A|B|C|D|E|F|G|战略)\+?轮",
]

_NON_FUNDING_NOISE_PATTERNS = [
    r"招聘",
    r"校招",
    r"社招",
    r"财报",
    r"营收",
    r"利润",
    r"人事任命",
    r"内部信",
]


def is_funding_related_text(text: str, details: dict | None = None) -> bool:
    details = details or parse_funding_details(text)
    if details.get("amount") or details.get("round") or details.get("investors"):
        return True

    return any(re.search(pattern, text, re.IGNORECASE) for pattern in _FUNDING_SIGNAL_PATTERNS)


def funding_confidence(
    text: str,
    details: dict | None = None,
    base: float = 0.300,
    source_bonus: float = 0.0,
) -> float:
    details = details or parse_funding_details(text)
    score = base + source_bonus
    if details.get("amount"):
        score += 0.220
    if details.get("round"):
        score += 0.160
    if details.get("investors"):
        score += 0.140
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in _FUNDING_SIGNAL_PATTERNS):
        score += 0.080
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in _NON_FUNDING_NOISE_PATTERNS):
        score -= 0.080
    return max(0.050, min(score, 0.950))


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
