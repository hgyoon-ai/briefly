from ..utils import make_hash, normalize_text


def dedupe_items(items):
    seen = set()
    deduped = []
    for item in items:
        key = item.get("url") or item.get("title")
        if not key:
            continue
        signature = make_hash(normalize_text(key))
        if signature in seen:
            continue
        seen.add(signature)
        deduped.append(item)
    return deduped
