from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

def name_hash(full_name: str) -> str:
    # Store only a hash for privacy. Change to return the raw name if you prefer.
    return hashlib.sha256(full_name.strip().lower().encode("utf-8")).hexdigest()

@dataclass
class IssuedRecord:
    certificate_id: str
    name_hash: str
    event_title: str
    event_date: str
    location: str
    issued_at: str

def write_manifest(path: str | Path, issued: List[IssuedRecord], meta: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": meta,
        "issued": [asdict(r) for r in issued],
    }
    p.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
