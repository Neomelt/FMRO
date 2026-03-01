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
    "投资者关系",
    "使用帮助",
    "防骗指南",
    "消息通知",
    "账号与安全中心",
    "营业执照",
    "许可证",
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
    "ai",
    "agent",
    "大模型",
    "llm",
    "智能体",
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


def _has_private_use_chars(text: str) -> bool:
    return any("\ue000" <= ch <= "\uf8ff" for ch in text)


def looks_like_job_title(text: str | None) -> bool:
    title = clean_text(text)
    if len(title) < 4 or len(title) > 80:
        return False

    if _has_private_use_chars(title):
        return False

    if "□" in title or "�" in title:
        return False

    lower = title.lower()
    if any(token in lower for token in BAD_TITLE_TOKENS):
        return False

    if "&#" in title:
        return False

    return any(token in lower for token in JOB_HINT_TOKENS)
