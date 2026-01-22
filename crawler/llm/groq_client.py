import json
import os

from groq import Groq

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

    return {
        "title": title,
        "snippet": snippet,
        "source": source,
        "published_at": published_at,
    }


def summarize_item(item, model="llama-3.1-8b-instant"):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return fallback_summary(item)

    client = Groq(api_key=api_key)
    payload = build_prompt(item)
    system_message = (
        "You are an analyst summarizing AI product and developer updates. "
        "Return compact JSON only."
    )
    user_message = (
        "Summarize the update as JSON with keys: summary (array of 3 short sentences), "
        "why (one sentence), topics (array of 2-5 tags), status (NEW|ONGOING|SHIFTING). "
        f"Input: {json.dumps(payload, ensure_ascii=False)}"
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.4,
        )
        content = response.choices[0].message.content
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
