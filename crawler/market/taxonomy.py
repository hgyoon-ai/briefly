TYPE_RAW_CHOICES = [
    "출시",
    "제휴",
    "시스템",
    "규제",
    "특허",
    "리서치",
    "기타",
]

AREA_RAW_CHOICES = [
    "리스크",
    "AML",
    "상담",
    "리서치",
    "트레이딩",
    "브로커리지",
    "WM",
    "기타",
]

TYPE_GROUP_MAP = {
    "출시": "제품/기능",
    "제휴": "제휴/협업",
    "시스템": "운영/시스템",
    "규제": "대외/인사이트",
    "특허": "대외/인사이트",
    "리서치": "대외/인사이트",
    "기타": "대외/인사이트",
}

AREA_GROUP_MAP = {
    "리스크": "리스크/컴플",
    "AML": "리스크/컴플",
    "상담": "고객/상담",
    "리서치": "투자/리서치",
    "트레이딩": "거래/브로커리지",
    "브로커리지": "거래/브로커리지",
    "WM": "자산관리(WM)",
    "기타": "투자/리서치",
}


def map_type_group(value):
    return TYPE_GROUP_MAP.get(value, "대외/인사이트")


def map_area_groups(values):
    if not values:
        return []
    seen = []
    for item in values:
        group = AREA_GROUP_MAP.get(item, "투자/리서치")
        if group not in seen:
            seen.append(group)
    return seen
