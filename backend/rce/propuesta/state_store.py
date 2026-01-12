import json, os
from datetime import datetime, timezone
from typing import Any, Dict
from pathlib import Path

SESSIONS_DIR = "/app/sessions_propuesta"

def _path(ruc: str) -> str:
    Path(SESSIONS_DIR).mkdir(parents=True, exist_ok=True)
    return os.path.join(SESSIONS_DIR, f"{ruc}.json")

def load_state(ruc: str) -> Dict[str, Any]:
    p = _path(ruc)
    if not os.path.exists(p):
        return {"ruc": ruc}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(ruc: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    st = load_state(ruc)
    st.update(patch)
    st["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(_path(ruc), "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)
    return st

def token_is_valid(st: Dict[str, Any]) -> bool:
    token = st.get("token")
    exp = st.get("token_expires_at")
    if not token or not exp:
        return False
    try:
        exp_dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
    except Exception:
        return False
    return exp_dt > datetime.now(timezone.utc)
