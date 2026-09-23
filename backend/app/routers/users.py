from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import User
from app.schemas.users import UserAdminResponse, UserAdminUpdate

router = APIRouter(prefix="/admin/users", tags=["Admin users"])


@router.get("", response_model=list[UserAdminResponse])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc())).all())


@router.patch("/{user_id}", response_model=UserAdminResponse)
def update_user_role(user_id: int, payload: UserAdminUpdate, _: User = Depends(require_admin), db: Session = Depends(get_db)) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, current_user: User = Depends(require_admin), db: Session = Depends(get_db)) -> None:
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя удалить текущего администратора")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    db.delete(user)
    db.commit()
