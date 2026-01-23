import json
import os

from openai import OpenAI

from ..config import (
    OPENAI_ITEM_MODEL_LONG,
    OPENAI_ITEM_MODEL_SHORT,
    OPENAI_ITEM_MODEL_THRESHOLD,
    OPENAI_ISSUE_MODEL,
    OPENAI_ITEM_MODEL,
    OPENAI_TEMPERATURE_ISSUE,
    OPENAI_TEMPERATURE_ITEM,
)
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


def build_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def call_openai(messages, model, temperature=None):
    client = build_client()
    if not client:
        return None, "OPENAI_API_KEY not set"
    try:
        params = {
            "model": model,
            "messages": messages,
        }
        if temperature is not None:
            params["temperature"] = temperature
        response = client.chat.completions.create(**params)
        return response, None
    except Exception as exc:
        return None, str(exc)


def summarize_item(item, model=None):
    payload = build_prompt(item)
    if model:
        model_name = model
    else:
        prompt_text = f"{payload.get('title', '')} {payload.get('snippet', '')}".strip()
        if len(prompt_text) >= OPENAI_ITEM_MODEL_THRESHOLD:
            model_name = OPENAI_ITEM_MODEL_LONG
        else:
            model_name = OPENAI_ITEM_MODEL_SHORT or OPENAI_ITEM_MODEL
    prompt = (
        "AI 제품/개발 업데이트를 요약하는 분석가입니다. "
        "한국어로만 응답하세요. JSON만 반환하세요. "
        "키: summary(짧은 문장 3개 배열), why(한 문장), topics(2-5개 태그), "
        "status(NEW|ONGOING|SHIFTING), importanceScore(1-10 정수). "
        "importanceScore는 중요도/영향도를 반영하세요. "
        f"Input: {json.dumps(payload, ensure_ascii=False)}"
    )

    response, error = call_openai(
        messages=[
            {"role": "system", "content": "You output only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        model=model_name,
        temperature=OPENAI_TEMPERATURE_ITEM,
    )
    if error or response is None:
        print(f"[LLM] OpenAI summary failed, using fallback: {error}")
        return fallback_summary(item)

    try:
        content = response.choices[0].message.content or ""
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
        print(f"[LLM] OpenAI summary failed, using fallback: {exc}")
        return fallback_summary(item)


def fallback_issue_summary(items, max_items=5):
    issues = []
    for idx, item in enumerate(items[:max_items], start=1):
        topic = (item.get("topics") or ["AI"])[0]
        related = []
        if item.get("title") and item.get("url"):
            related.append(
                {
                    "title": item.get("title"),
                    "source": item.get("source"),
                    "url": item.get("url"),
                }
            )
        issues.append(
            {
                "id": f"issue_{idx:03d}",
                "status": item.get("status") or "NEW",
                "title": f"{topic} 업데이트 집중",
                "summary": item.get("summary", ["최근 업데이트가 이어지고 있음"])[0],
                "articleCount": 1,
                "relatedArticles": related,
            }
        )
    return issues


def summarize_issues(items, model=None, max_items=5):
    if not items:
        return fallback_issue_summary(items, max_items=max_items)

    model_name = model or OPENAI_ISSUE_MODEL
    samples = []
    for item in items[:20]:
        samples.append(
            {
                "title": normalize_text(item.get("title")),
                "summary": " ".join(item.get("summary", [])[:2]),
                "topics": item.get("topics", []),
                "status": item.get("status"),
                "importanceScore": item.get("importanceScore"),
                "source": item.get("source"),
                "url": item.get("url"),
            }
        )

    prompt = (
        "주간/월간 AI 업데이트를 주요 이슈로 재요약하세요. "
        "한국어로만 응답하고 JSON 배열만 반환하세요. "
        "각 항목은 id, status(NEW|ONGOING|SHIFTING), title, summary, articleCount, "
        "relatedArticles(최대 3개, source/title/url 포함) 키를 포함해야 합니다. "
        "주제 다양성을 확보하고 같은 주제 반복을 피하세요. "
        f"Input: {json.dumps(samples, ensure_ascii=False)}"
    )

    response, error = call_openai(
        messages=[
            {"role": "system", "content": "You output only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        model=model_name,
        temperature=OPENAI_TEMPERATURE_ISSUE,
    )
    if error or response is None:
        print(f"[LLM] OpenAI issues summary failed, using fallback: {error}")
        return fallback_issue_summary(items, max_items=max_items)

    try:
        content = response.choices[0].message.content or ""
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
            issue.setdefault("relatedArticles", [])
        return trimmed
    except Exception as exc:
        print(f"[LLM] OpenAI issues summary failed, using fallback: {exc}")
        return fallback_issue_summary(items, max_items=max_items)
