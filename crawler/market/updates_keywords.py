from crawler.market.keywords import is_ai_candidate, is_soft_candidate, normalize_for_match


STRONG_UPDATE_KEYWORDS = [
    "신규",
    "추가",
    "오픈",
    "출시",
    "런칭",
    "개편",
    "전면",
    "리뉴얼",
    "개선",
    "고도화",
    "적용",
    "지원",
    "확대",
    "연동",
    "도입",
    "전환",
    "통합",
    "변경",
    "업데이트",
    "업그레이드",
    "개통",
    "점검",
    "장애",
    "오류",
    "중단",
    "지연",
    "복구",
    "보안",
    "인증",
    "간편인증",
    "생체",
    "피싱",
    "탐지",
    "차단",
    "보호",
    "주문",
    "거래",
    "트레이딩",
    "차트",
    "알림",
    "환전",
    "수수료",
    "계좌",
    "해외주식",
    "ETF",
    "공모주",
    "청약",
    "대출",
    "신용",
    "담보",
    "MTS",
]


SOFT_UPDATE_KEYWORDS = [
    "기능",
    "화면",
    "UX",
    "UI",
    "성능",
    "안정",
    "속도",
    "알림",
    "편의",
    "개인화",
]


def is_updates_candidate(text):
    lowered = normalize_for_match(text)
    if not lowered:
        return False

    # Exclude AI-related items from this dataset.
    if is_ai_candidate(lowered) or is_soft_candidate(lowered):
        return False

    return any(keyword.lower() in lowered for keyword in STRONG_UPDATE_KEYWORDS) or any(
        keyword.lower() in lowered for keyword in SOFT_UPDATE_KEYWORDS
    )
