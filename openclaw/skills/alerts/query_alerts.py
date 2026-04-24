"""
Skill: query_alerts
Rule-based alerts: price_drop, stockout, bsr_drop, image_change, new_entrant, exit.
"""
from __future__ import annotations
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from dotenv import load_dotenv
load_dotenv()
from lib.db import supabase


SKILL = {
    "name": "query_alerts",
    "group": "alerts",
    "description": (
        "Return active alerts filtered by category/severity/days. "
        "Alert types: price_drop, stockout, bsr_drop, image_change, new_entrant, exit. "
        "Severity: low|medium|high."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {"type": "string"},
            "severity": {"type": "string", "enum": ["low", "medium", "high", "any"], "default": "any"},
            "days":     {"type": "integer", "default": 1, "minimum": 1, "maximum": 14},
            "limit":    {"type": "integer", "default": 30},
        },
        "required": [],
    },
}


def run(category: str | None = None, severity: str = "any", days: int = 1, limit: int = 30) -> list[dict]:
    since = (date.today() - timedelta(days=days)).isoformat()
    q = (supabase.table("alerts")
         .select("snapshot_date,asin,browse_node,alert_type,severity,message,metadata_json")
         .gte("snapshot_date", since).order("snapshot_date", desc=True).limit(limit))
    if category:
        q = q.eq("browse_node", category)
    if severity != "any":
        q = q.eq("severity", severity)
    return q.execute().data or []


def main() -> None:
    if "--schema" in sys.argv:
        print(json.dumps(SKILL, indent=2)); return
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(run(**args), default=str))


if __name__ == "__main__":
    main()
