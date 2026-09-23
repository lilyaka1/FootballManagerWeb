import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.database import SessionLocal
from app.models import ApiCache
from app.services.sync_service import FootballSyncService
from sqlalchemy import select


INPUT_PATH = Path(__file__).resolve().parents[1] / "api_data" / "api_football_raw.json"


def import_file() -> dict[str, int]:
    payload = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    imported = 0
    with SessionLocal() as db:
        for item in payload.get("responses", []):
            cached = db.scalar(select(ApiCache).where(ApiCache.cache_key == item["cache_key"]))
            if cached:
                cached.data = item["data"]
                cached.endpoint = item["endpoint"]
                cached.entity_type = item["entity_type"]
            else:
                db.add(ApiCache(
                    cache_key=item["cache_key"],
                    endpoint=item["endpoint"],
                    entity_type=item["entity_type"],
                    data=item["data"],
                ))
            imported += 1
        db.commit()
        service = FootballSyncService(get_settings(), db)
        service.clear_unverified_catalog_fields()
        result = service.reprocess_cached_data()
    return {"raw_responses_imported": imported, **result}


if __name__ == "__main__":
    print(import_file())
