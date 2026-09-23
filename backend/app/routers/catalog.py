from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.auth import require_admin
from app.database import get_db
from app.models import Club, Player, Transfer, User
from app.models import ApiCache
from app.schemas.catalog import (
    ClubCreate,
    ClubDetailsResponse,
    ClubResponse,
    PlayerCreate,
    PlayerDetailsResponse,
    PlayerResponse,
    TransferCreate,
    TransferResponse,
)

players_router = APIRouter(prefix="/players", tags=["Players"])
clubs_router = APIRouter(prefix="/clubs", tags=["Clubs"])
transfers_router = APIRouter(prefix="/transfers", tags=["Transfers"])


def _transfer_view(transfer: Transfer) -> dict:
    return {
        "id": transfer.id,
        "external_id": transfer.external_id,
        "player_id": transfer.player_id,
        "from_club_id": transfer.from_club_id,
        "to_club_id": transfer.to_club_id,
        "transfer_date": transfer.transfer_date,
        "fee": transfer.fee,
        "currency": transfer.currency,
        "transfer_type": transfer.transfer_type,
        "source": transfer.source,
        "player_name": transfer.player.name if transfer.player else None,
        "from_club_name": transfer.from_club.name if transfer.from_club else "Свободный агент",
        "to_club_name": transfer.to_club.name if transfer.to_club else "Клуб не указан",
    }


@players_router.get("", response_model=list[PlayerResponse])
def list_players(
    search: str | None = None,
    position: str | None = None,
    nationality: str | None = None,
    sort: str = Query(default="name_asc", pattern="^(name_asc|name_desc|value_desc|value_asc)$"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=8, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[Player]:
    order_by = Player.name.asc() if sort == "name_asc" else Player.name.desc() if sort == "name_desc" else Player.market_value.desc().nullslast() if sort == "value_desc" else Player.market_value.asc().nullsfirst()
    query = select(Player).options(selectinload(Player.current_club)).order_by(order_by).offset((page - 1) * limit).limit(limit)
    if search:
        query = query.where(Player.name.ilike(f"%{search}%"))
    if position:
        query = query.where(Player.position.ilike(f"%{position}%"))
    if nationality:
        query = query.where(Player.nationality.ilike(f"%{nationality}%"))
    return [{**PlayerResponse.model_validate(player).model_dump(), "current_club_name": player.current_club.name if player.current_club else None} for player in db.scalars(query).all()]


@players_router.get("/{player_id}/api-data", tags=["External API data"])
def get_player_api_data(player_id: int, db: Session = Depends(get_db)) -> dict:
    player = db.get(Player, player_id)
    if not player or player.external_id is None:
        raise HTTPException(status_code=404, detail="Raw данные игрока не найдены")
    for cached in db.scalars(select(ApiCache).where(ApiCache.endpoint == "/players")).all():
        for row in cached.data.get("response", []):
            if (row.get("player") or {}).get("id") == player.external_id:
                return row
    raise HTTPException(status_code=404, detail="Raw данные игрока не найдены")


@players_router.get("/{player_id}", response_model=PlayerDetailsResponse)
def get_player(player_id: int, db: Session = Depends(get_db)) -> Player:
    player = db.scalar(select(Player).options(selectinload(Player.transfers).selectinload(Transfer.player), selectinload(Player.transfers).selectinload(Transfer.from_club), selectinload(Player.transfers).selectinload(Transfer.to_club)).where(Player.id == player_id))
    if not player:
        raise HTTPException(status_code=404, detail="Футболист не найден")
    player_data = PlayerDetailsResponse.model_validate(player).model_dump()
    player_data["current_club_name"] = player.current_club.name if player.current_club else None
    player_data["transfers"] = [_transfer_view(transfer) for transfer in player.transfers]
    return player_data


@players_router.post("", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
def create_player(payload: PlayerCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> Player:
    player = Player(**payload.model_dump())
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


@players_router.put("/{player_id}", response_model=PlayerResponse)
def update_player(player_id: int, payload: PlayerCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> Player:
    player = db.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Футболист не найден")
    for key, value in payload.model_dump().items():
        setattr(player, key, value)
    db.commit()
    db.refresh(player)
    return player


@players_router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(player_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> None:
    player = db.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Футболист не найден")
    db.delete(player)
    db.commit()


@clubs_router.get("", response_model=list[ClubResponse])
def list_clubs(
    search: str | None = None,
    country: str | None = None,
    league: str | None = None,
    sort: str = Query(default="name_asc", pattern="^(name_asc|name_desc|country_asc|squad_desc)$"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=8, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[Club]:
    squad_size = select(func.count(Player.id)).where(Player.current_club_id == Club.id).scalar_subquery()
    order_by = Club.name.asc() if sort == "name_asc" else Club.name.desc() if sort == "name_desc" else Club.country.asc().nullslast() if sort == "country_asc" else squad_size.desc()
    query = select(Club).order_by(order_by).offset((page - 1) * limit).limit(limit)
    if search:
        query = query.where(Club.name.ilike(f"%{search}%"))
    if country:
        query = query.where(Club.country.ilike(f"%{country}%"))
    if league:
        query = query.where(Club.league.ilike(f"%{league}%"))
    return list(db.scalars(query).all())


@clubs_router.get("/{club_id}/api-data", tags=["External API data"])
def get_club_api_data(club_id: int, db: Session = Depends(get_db)) -> dict:
    club = db.get(Club, club_id)
    if not club or club.external_id is None:
        raise HTTPException(status_code=404, detail="Raw данные клуба не найдены")
    for cached in db.scalars(select(ApiCache).where(ApiCache.endpoint == "/teams")).all():
        for row in cached.data.get("response", []):
            if (row.get("team") or {}).get("id") == club.external_id:
                return row
    raise HTTPException(status_code=404, detail="Raw данные клуба не найдены")


@clubs_router.get("/{club_id}", response_model=ClubDetailsResponse)
def get_club(club_id: int, db: Session = Depends(get_db)) -> Club:
    club = db.scalar(select(Club).options(selectinload(Club.current_players), selectinload(Club.incoming_transfers).selectinload(Transfer.player), selectinload(Club.incoming_transfers).selectinload(Transfer.from_club), selectinload(Club.incoming_transfers).selectinload(Transfer.to_club), selectinload(Club.outgoing_transfers).selectinload(Transfer.player), selectinload(Club.outgoing_transfers).selectinload(Transfer.from_club), selectinload(Club.outgoing_transfers).selectinload(Transfer.to_club)).where(Club.id == club_id))
    if not club:
        raise HTTPException(status_code=404, detail="Клуб не найден")
    club_data = ClubDetailsResponse.model_validate(club).model_dump()
    club_data["current_players"] = [PlayerResponse.model_validate(player).model_dump() for player in club.current_players]
    club_data["incoming_transfers"] = [_transfer_view(transfer) for transfer in club.incoming_transfers]
    club_data["outgoing_transfers"] = [_transfer_view(transfer) for transfer in club.outgoing_transfers]
    return club_data


@clubs_router.post("", response_model=ClubResponse, status_code=status.HTTP_201_CREATED)
def create_club(payload: ClubCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> Club:
    club = Club(**payload.model_dump())
    db.add(club)
    db.commit()
    db.refresh(club)
    return club


@clubs_router.put("/{club_id}", response_model=ClubResponse)
def update_club(club_id: int, payload: ClubCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> Club:
    club = db.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Клуб не найден")
    for key, value in payload.model_dump().items():
        setattr(club, key, value)
    db.commit()
    db.refresh(club)
    return club


@clubs_router.delete("/{club_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_club(club_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> None:
    club = db.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Клуб не найден")
    db.delete(club)
    db.commit()


@transfers_router.get("", response_model=list[TransferResponse])
def list_transfers(
    player_id: int | None = None,
    club_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    fee_min: float | None = Query(default=None, ge=0),
    fee_max: float | None = Query(default=None, ge=0),
    sort: str = Query(default="date_desc", pattern="^(date_desc|date_asc|fee_desc|fee_asc)$"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=8, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = select(Transfer).options(selectinload(Transfer.player), selectinload(Transfer.from_club), selectinload(Transfer.to_club))
    if player_id:
        query = query.where(Transfer.player_id == player_id)
    if club_id:
        query = query.where(or_(Transfer.from_club_id == club_id, Transfer.to_club_id == club_id))
    if date_from:
        query = query.where(Transfer.transfer_date >= date_from)
    if date_to:
        query = query.where(Transfer.transfer_date <= date_to)
    if fee_min is not None:
        query = query.where(Transfer.fee >= fee_min)
    if fee_max is not None:
        query = query.where(Transfer.fee <= fee_max)
    order_by = Transfer.transfer_date.desc() if sort == "date_desc" else Transfer.transfer_date.asc() if sort == "date_asc" else Transfer.fee.desc() if sort == "fee_desc" else Transfer.fee.asc()
    transfers = list(db.scalars(query.order_by(order_by).offset((page - 1) * limit).limit(limit)).all())
    return [_transfer_view(transfer) for transfer in transfers]


@transfers_router.get("/{transfer_id}/api-data", tags=["External API data"])
def get_transfer_api_data(transfer_id: int, db: Session = Depends(get_db)) -> dict:
    transfer = db.scalar(select(Transfer).options(selectinload(Transfer.player)).where(Transfer.id == transfer_id))
    if not transfer or not transfer.player or transfer.player.external_id is None:
        raise HTTPException(status_code=404, detail="Raw данные трансфера не найдены")
    for cached in db.scalars(select(ApiCache).where(ApiCache.endpoint == "/transfers")).all():
        for row in cached.data.get("response", []):
            if (row.get("player") or {}).get("id") == transfer.player.external_id:
                for item in row.get("transfers", []):
                    if item.get("date") == transfer.transfer_date.isoformat() if transfer.transfer_date else False:
                        return {"player": row.get("player"), "update": row.get("update"), "transfer": item}
    raise HTTPException(status_code=404, detail="Raw данные трансфера не найдены")


@transfers_router.get("/{transfer_id}", response_model=TransferResponse)
def get_transfer(transfer_id: int, db: Session = Depends(get_db)) -> Transfer:
    transfer = db.scalar(select(Transfer).options(selectinload(Transfer.player), selectinload(Transfer.from_club), selectinload(Transfer.to_club)).where(Transfer.id == transfer_id))
    if not transfer:
        raise HTTPException(status_code=404, detail="Трансфер не найден")
    return _transfer_view(transfer)


@transfers_router.post("", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
def create_transfer(payload: TransferCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> Transfer:
    transfer = Transfer(**payload.model_dump())
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    return transfer


@transfers_router.put("/{transfer_id}", response_model=TransferResponse)
def update_transfer(transfer_id: int, payload: TransferCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> Transfer:
    transfer = db.get(Transfer, transfer_id)
    if not transfer:
        raise HTTPException(status_code=404, detail="Трансфер не найден")
    for key, value in payload.model_dump().items():
        setattr(transfer, key, value)
    db.commit()
    db.refresh(transfer)
    return transfer


@transfers_router.delete("/{transfer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transfer(transfer_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> None:
    transfer = db.get(Transfer, transfer_id)
    if not transfer:
        raise HTTPException(status_code=404, detail="Трансфер не найден")
    db.delete(transfer)
    db.commit()
