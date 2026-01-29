import json
from pathlib import Path


def _load_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_run_and_history(latest_path, history_path, run_payload, limit=7):
    latest_path = Path(latest_path)
    history_path = Path(history_path)

    run_id = run_payload.get("id")
    if not run_id:
        run_id = run_payload.get("ts") or "unknown"
        run_payload = {**run_payload, "id": run_id}

    history = _load_json(history_path)
    if not isinstance(history, list):
        history = []

    next_history = [run_payload]
    for entry in history:
        if not isinstance(entry, dict):
            continue
        if entry.get("id") == run_id:
            continue
        next_history.append(entry)
        if len(next_history) >= limit:
            break

    _write_json(latest_path, run_payload)
    _write_json(history_path, next_history)
