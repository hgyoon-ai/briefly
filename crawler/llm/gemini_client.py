import json
import os

import google.generativeai as genai

from ..utils import normalize_text


KEYWORDS = {
    "agent": "Agent",
    "rag": "RAG",
    "tool": "Tool Use",
    "function": "Function Calling",
    "benchmark": "Benchmark",
    "multimodal": "Multimodal",
    "vision": "Multimodal",
    "audio": "Multimodal",
    "inference": "Inference",
    "eval": "Evaluation",
    "fine-tuning": "Fine-tuning",
    "finetune": "Fine-tuning",
    "alignment": "Alignment",
}


def default_topics(text):
    lowered = text.lower()
    found = []
    for key, label in KEYWORDS.items():
        if key in lowered and label not in found:
            found.append(label)
    return found or ["AI"]


def fallback_summary(item):
    title = normalize_text(item.get("title"))
    snippet = normalize_text(item.get("snippet"))
    summary_lines = [title]
    if snippet:
        summary_lines.append(snippet[:120])
    while len(summary_lines) < 3:
        summary_lines.append("관련 업데이트가 이어지고 있음")

    topics = default_topics(f"{title} {snippet}")
    return {
        "summary": summary_lines[:3],
        "why": "개발 현황 파악에 직접적인 영향을 주는 업데이트",
        "topics": topics,
        "status": "NEW",
    }


def build_prompt(item):
    title = normalize_text(item.get("title"))
    snippet = normalize_text(item.get("snippet"))
    source = normalize_text(item.get("source"))
    published_at = item.get("published_at")
    if published_at:
        published_at = published_at.isoformat()

    return {
        "title": title,
        "snippet": snippet,
        "source": source,
        "published_at": published_at,
    }


def summarize_item(item, model="gemini-2.0-flash"):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return fallback_summary(item)

    genai.configure(api_key=api_key)
    payload = build_prompt(item)
    prompt = (
        "You are an analyst summarizing AI product and developer updates. "
        "Return JSON only with keys: summary (array of 3 short sentences), "
        "why (one sentence), topics (array of 2-5 tags), status (NEW|ONGOING|SHIFTING). "
        f"Input: {json.dumps(payload, ensure_ascii=False)}"
    )

    try:
        client = genai.GenerativeModel(model)
        response = client.generate_content(prompt)
        content = response.text
        result = json.loads(content)
        if not isinstance(result.get("summary"), list):
            raise ValueError("Invalid summary")
        return {
            "summary": result.get("summary")[:3],
            "why": result.get("why") or "",
            "topics": result.get("topics") or default_topics(payload["title"]),
            "status": result.get("status") or "NEW",
        }
    except Exception:
        return fallback_summary(item)
