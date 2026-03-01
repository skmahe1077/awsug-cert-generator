from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Any

def read_csv(path: str | Path) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"CSV not found: {p}")
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            # Normalize keys
            rows.append({(k or "").strip().lower(): (v or "").strip() for k, v in row.items()})
        if not rows:
            raise ValueError("CSV contains no rows.")
        return rows

def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
