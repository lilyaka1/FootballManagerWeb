from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Club, Player, Transfer
from app.schemas.catalog import SummaryResponse

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=SummaryResponse)
def summary(db: Session = Depends(get_db)) -> SummaryResponse:
    total_fee = db.scalar(select(func.coalesce(func.sum(Transfer.fee), 0)))
    return SummaryResponse(
        players_count=db.scalar(select(func.count(Player.id))) or 0,
        clubs_count=db.scalar(select(func.count(Club.id))) or 0,
        transfers_count=db.scalar(select(func.count(Transfer.id))) or 0,
        total_fee=Decimal(str(total_fee)),
    )


@router.get("/transfers-by-year")
def transfers_by_year(db: Session = Depends(get_db)) -> list[dict[str, int]]:
    rows = db.execute(
        select(func.extract("year", Transfer.transfer_date).label("year"), func.count(Transfer.id))
        .where(Transfer.transfer_date.is_not(None))
        .group_by("year")
        .order_by("year")
    )
    return [{"year": int(year), "count": count} for year, count in rows]
