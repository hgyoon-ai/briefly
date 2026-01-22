import requests

from ..config import HF_TRENDING_URL, MAX_PER_SOURCE
from ..utils import normalize_text, parse_datetime


def fetch_huggingface_trending(timezone):
    params = {
        "sort": "trending",
        "direction": -1,
        "limit": MAX_PER_SOURCE["huggingface"],
    }
    response = requests.get(HF_TRENDING_URL, params=params, timeout=20)
    response.raise_for_status()
    models = response.json()
    items = []
    for model in models:
        published_at = parse_datetime(model.get("lastModified"), timezone)
        items.append(
            {
                "title": normalize_text(model.get("modelId")),
                "url": f"https://huggingface.co/{model.get('modelId')}",
                "source": "Hugging Face Hub",
                "published_at": published_at,
                "snippet": normalize_text(model.get("pipeline_tag") or model.get("library_name")),
                "tab": "ai",
                "kind": "huggingface",
            }
        )
    return items
