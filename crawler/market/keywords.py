import re


STRONG_KEYWORDS = [
    "ai",
    "인공지능",
    "gpt",
    "copilot",
    "agent",
    "llm",
    "생성형",
    "챗봇",
    "추천",
    "요약",
    "자동화",
    "자동 요약",
    "머신러닝",
    "딥러닝",
    "리스크모델",
    "리스크",
    "aml",
    "이상거래",
    "fraud",
]

SOFT_KEYWORDS = [
    "디지털",
    "플랫폼",
    "모델",
    "데이터",
    "분석",
    "검색",
    "서비스",
]


def normalize_text(value):
    if not value:
        return ""
    cleaned = re.sub(r"\s+", " ", value)
    return cleaned.strip().lower()


def is_ai_candidate(text):
    lowered = normalize_text(text)
    return any(keyword in lowered for keyword in STRONG_KEYWORDS)


def is_soft_candidate(text):
    lowered = normalize_text(text)
    return any(keyword in lowered for keyword in SOFT_KEYWORDS)
