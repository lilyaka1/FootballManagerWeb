from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user
from app.database import get_db
from app.models import Favorite, Player, User
from app.schemas.favorites import FavoriteResponse

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get("", response_model=list[FavoriteResponse])
def list_favorites(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Favorite]:
    query = select(Favorite).options(joinedload(Favorite.player)).where(Favorite.user_id == current_user.id)
    return list(db.scalars(query).all())


@router.post("/{player_id}", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
def add_favorite(player_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Favorite:
    player = db.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Футболист не найден")

    existing = db.scalar(select(Favorite).where(Favorite.user_id == current_user.id, Favorite.player_id == player_id))
    if existing:
        return existing

    favorite = Favorite(user_id=current_user.id, player_id=player_id)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    favorite.player = player
    return favorite


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(player_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    favorite = db.scalar(select(Favorite).where(Favorite.user_id == current_user.id, Favorite.player_id == player_id))
    if not favorite:
        raise HTTPException(status_code=404, detail="Футболист отсутствует в избранном")
    db.delete(favorite)
    db.commit()
