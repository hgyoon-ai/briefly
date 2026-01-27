import json
import os

from openai import OpenAI

from .taxonomy import AREA_RAW_CHOICES, TYPE_RAW_CHOICES


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


def build_prompt(items):
    type_list = ", ".join(TYPE_RAW_CHOICES)
    area_list = ", ".join(AREA_RAW_CHOICES)
    prompt = (
        "너는 증권사 공식 공시/보도자료를 분류하는 분석가다. "
        "한국어로만 응답하고 JSON 배열만 반환해라. "
        "각 항목은 id, keep(true/false), oneLiner(한두 문장), "
        f"type_raw({type_list}), areas_raw(배열, {area_list}), confidence(0~1) 키를 포함해야 한다. "
        "AI/데이터/자동화/리스크/AML/챗봇/요약/추천 등과 직접 관련 없는 항목은 keep=false로 두어라. "
        "타입/영역은 반드시 목록에서만 선택한다. "
        f"Input: {json.dumps(items, ensure_ascii=False)}"
    )
    return prompt


def call_openai(messages, model):
    client = build_client()
    if not client:
        raise RuntimeError("OPENAI_API_KEY not set")
    response = client.chat.completions.create(model=model, messages=messages)
    return response


def parse_response(content):
    extracted = extract_json(content)
    if not extracted:
        raise ValueError("Invalid JSON response")
    parsed = json.loads(extracted)
    if not isinstance(parsed, list):
        raise ValueError("Expected JSON array")
    return parsed


def enrich_batch(items, model="gpt-5-mini"):
    prompt = build_prompt(items)
    response = call_openai(
        messages=[
            {"role": "system", "content": "You output only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        model=model,
    )
    content = response.choices[0].message.content or ""
    return parse_response(content)


def enrich_items(items, model="gpt-5-mini", batch_size=12):
    results = {}
    index = 0
    while index < len(items):
        batch = items[index : index + batch_size]
        try:
            enriched = enrich_batch(batch, model=model)
        except Exception:
            if batch_size > 1:
                return {
                    **results,
                    **enrich_items(batch, model=model, batch_size=max(1, batch_size // 2)),
                    **enrich_items(items[index + batch_size :], model=model, batch_size=batch_size),
                }
            raise
        for entry in enriched:
            entry_id = entry.get("id")
            if entry_id:
                results[entry_id] = entry
        index += batch_size
    return results
