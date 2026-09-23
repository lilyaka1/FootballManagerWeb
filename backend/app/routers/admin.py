from fastapi import APIRouter, Depends, HTTPException, status
import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.config import get_settings
from app.database import get_db
from app.models import ApiCache, User
from app.schemas.sync import SyncRequest, SyncResult
from app.services.demo_seed import remove_curated_demo_data, remove_generated_players
from app.services.sync_service import FootballSyncService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/sync", response_model=SyncResult)
async def sync_data(
    payload: SyncRequest,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> SyncResult:
    try:
        return await FootballSyncService(get_settings(), db).sync(payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    except httpx.HTTPStatusError as error:
        db.rollback()
        if error.response.status_code == 429:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Лимит API-Football исчерпан. Raw-ответы уже сохранены, повторите позже.") from error
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Ошибка API-Football: {error}") from error
    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Ошибка API-Football: {error}") from error


@router.post("/seed-demo")
async def seed_demo(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict[str, int | str]:
    raise HTTPException(status_code=status.HTTP_410_GONE, detail="Синтетический seed отключен. Используйте /admin/sync для реальных данных API-Football.")


@router.delete("/demo-generated")
def delete_demo_generated(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict[str, int | str]:
    return {"status": "completed", "removed_players": remove_generated_players(db)}


@router.delete("/curated-demo")
def delete_curated_demo(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict[str, int | str]:
    return {"status": "completed", **remove_curated_demo_data(db)}


@router.get("/cache-status")
def cache_status(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict[str, int]:
    return {"raw_responses": db.scalar(select(func.count(ApiCache.id))) or 0}


@router.post("/reprocess-cache")
def reprocess_cache(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict[str, int | str]:
    return {"status": "completed", **FootballSyncService(get_settings(), db).reprocess_cached_data()}
