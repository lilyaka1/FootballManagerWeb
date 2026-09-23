import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models import ApiCache


OUTPUT_PATH = Path(__file__).resolve().parents[1] / "api_data" / "api_football_raw.json"


def export_cache() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SessionLocal() as db:
        rows = db.scalars(select(ApiCache).order_by(ApiCache.id)).all()
        payload = {
            "source": "API-Football",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "response_count": len(rows),
            "responses": [
                {
                    "cache_key": row.cache_key,
                    "endpoint": row.endpoint,
                    "entity_type": row.entity_type,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                    "data": row.data,
                }
                for row in rows
            ],
        }
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(rows)


if __name__ == "__main__":
    print(f"Exported {export_cache()} API responses to {OUTPUT_PATH}")
