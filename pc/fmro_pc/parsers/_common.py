from __future__ import annotations

from html import unescape

CITIES = ["北京", "上海", "深圳", "杭州", "广州", "成都", "苏州", "南京", "武汉", "西安"]

BAD_TITLE_TOKENS = [
    "登录",
    "注册",
    "首页",
    "关于我们",
    "了解更多",
    "点击",
    "举报",
    "隐私",
    "协议",
    "二维码",
    "app下载",
]

JOB_HINT_TOKENS = [
    "工程师",
    "算法",
    "实习",
    "开发",
    "研发",
    "机器人",
    "slam",
    "感知",
    "控制",
    "导航",
]


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(unescape(value).split())


def infer_city(text: str | None) -> str | None:
    target = clean_text(text)
    for city in CITIES:
        if city in target:
            return city
    return None


def looks_like_job_title(text: str | None) -> bool:
    title = clean_text(text)
    if len(title) < 4 or len(title) > 80:
        return False

    lower = title.lower()
    if any(token in lower for token in BAD_TITLE_TOKENS):
        return False

    if "&#" in title:
        return False

    return any(token in lower for token in JOB_HINT_TOKENS)
