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
        "importanceScore": 5,
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


def extract_json(text):
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()
    start = min(
        [pos for pos in [cleaned.find("{"), cleaned.find("[")] if pos != -1],
        default=-1,
    )
    if start == -1:
        return None
    end = max(cleaned.rfind("}"), cleaned.rfind("]"))
    if end == -1:
        return None
    return cleaned[start : end + 1]


def summarize_item(item, model="gemini-2.5-flash"):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[LLM] GEMINI_API_KEY not set, using fallback summary.")
        return fallback_summary(item)

    genai.configure(api_key=api_key)
    payload = build_prompt(item)
    prompt = (
        "You are an analyst summarizing AI product and developer updates. "
        "Return JSON only with keys: summary (array of 3 short sentences), "
        "why (one sentence), topics (array of 2-5 tags), "
        "status (NEW|ONGOING|SHIFTING), importanceScore (1-10 integer). "
        "Score should reflect importance and impact. "
        f"Input: {json.dumps(payload, ensure_ascii=False)}"
    )

    try:
        client = genai.GenerativeModel(model)
        response = client.generate_content(prompt)
        content = response.text or ""
        extracted = extract_json(content)
        if not extracted:
            raise ValueError("Empty or invalid JSON payload")
        result = json.loads(extracted)
        if not isinstance(result.get("summary"), list):
            raise ValueError("Invalid summary")
        return {
            "summary": result.get("summary")[:3],
            "why": result.get("why") or "",
            "topics": result.get("topics") or default_topics(payload["title"]),
            "status": result.get("status") or "NEW",
            "importanceScore": int(result.get("importanceScore") or 5),
        }
    except Exception as exc:
        print(f"[LLM] Gemini summary failed, using fallback: {exc}")
        return fallback_summary(item)


def fallback_issue_summary(items, max_items=5):
    issues = []
    for idx, item in enumerate(items[:max_items], start=1):
        topic = (item.get("topics") or ["AI"])[0]
        issues.append(
            {
                "id": f"issue_{idx:03d}",
                "status": item.get("status") or "NEW",
                "title": f"{topic} 업데이트 집중",
                "summary": item.get("summary", ["최근 업데이트가 이어지고 있음"])[0],
                "articleCount": 1,
            }
        )
    return issues


def summarize_issues(items, model="gemini-2.5-flash", max_items=5):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not items:
        if not api_key:
            print("[LLM] GEMINI_API_KEY not set, using fallback issues.")
        return fallback_issue_summary(items, max_items=max_items)

    genai.configure(api_key=api_key)
    samples = []
    for item in items[:20]:
        samples.append(
            {
                "title": normalize_text(item.get("title")),
                "summary": " ".join(item.get("summary", [])[:2]),
                "topics": item.get("topics", []),
                "status": item.get("status"),
                "importanceScore": item.get("importanceScore"),
            }
        )

    prompt = (
        "You are summarizing weekly/monthly AI updates into diverse issues. "
        "Return JSON array with 2-5 items. Each item must include keys: "
        "id, status (NEW|ONGOING|SHIFTING), title, summary, articleCount. "
        "Ensure topic diversity (avoid repeating the same topic). "
        f"Input: {json.dumps(samples, ensure_ascii=False)}"
    )

    try:
        client = genai.GenerativeModel(model)
        response = client.generate_content(prompt)
        content = response.text or ""
        extracted = extract_json(content)
        if not extracted:
            raise ValueError("Empty or invalid JSON payload")
        result = json.loads(extracted)
        if not isinstance(result, list):
            raise ValueError("Invalid issues")
        trimmed = result[:max_items]
        for idx, issue in enumerate(trimmed, start=1):
            issue.setdefault("id", f"issue_{idx:03d}")
            issue.setdefault("status", "NEW")
            issue.setdefault("summary", "")
            issue.setdefault("articleCount", 1)
        return trimmed
    except Exception as exc:
        print(f"[LLM] Gemini issues summary failed, using fallback: {exc}")
        return fallback_issue_summary(items, max_items=max_items)
