from ..utils import normalize_text


CANONICAL_TAGS = [
    "agent tooling",
    "observability",
    "eval",
    "infra",
    "runtime",
    "editor",
    "codegen",
    "testing",
    "local-first",
    "vector db",
    "security",
    "data",
]

TAG_ALIASES = {
    "agent": "agent tooling",
    "agentic": "agent tooling",
    "orchestration": "agent tooling",
    "workflow": "agent tooling",
    "pipeline": "agent tooling",
    "observability": "observability",
    "tracing": "observability",
    "monitoring": "observability",
    "telemetry": "observability",
    "eval": "eval",
    "evaluation": "eval",
    "benchmark": "eval",
    "judge": "eval",
    "infra": "infra",
    "platform": "infra",
    "ops": "infra",
    "sre": "infra",
    "k8s": "infra",
    "kubernetes": "infra",
    "cloud": "infra",
    "runtime": "runtime",
    "executor": "runtime",
    "sandbox": "runtime",
    "vm": "runtime",
    "editor": "editor",
    "ide": "editor",
    "vscode": "editor",
    "codegen": "codegen",
    "code generation": "codegen",
    "copilot": "codegen",
    "testing": "testing",
    "test": "testing",
    "regression": "testing",
    "local-first": "local-first",
    "offline-first": "local-first",
    "vector": "vector db",
    "embedding": "vector db",
    "faiss": "vector db",
    "milvus": "vector db",
    "pgvector": "vector db",
    "security": "security",
    "auth": "security",
    "oauth": "security",
    "vuln": "security",
    "data": "data",
    "dataset": "data",
    "data quality": "data",
}


def _alias_match(term):
    return TAG_ALIASES.get(term)


def _keyword_match(text):
    matches = []
    lowered = text.lower()
    for keyword, tag in TAG_ALIASES.items():
        if keyword in lowered and tag not in matches:
            matches.append(tag)
    return matches


def normalize_tags(tags, text=None, max_tags=2):
    normalized = []
    for raw in tags or []:
        cleaned = normalize_text(raw).lower()
        mapped = _alias_match(cleaned)
        if mapped and mapped not in normalized:
            normalized.append(mapped)

    if text:
        for tag in _keyword_match(text):
            if tag not in normalized:
                normalized.append(tag)

    ordered = [tag for tag in CANONICAL_TAGS if tag in normalized]
    return ordered[:max_tags]
