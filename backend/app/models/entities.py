from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=UserRole.USER.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[int | None] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    birth_date: Mapped[date | None] = mapped_column(Date)
    nationality: Mapped[str | None] = mapped_column(String(80))
    position: Mapped[str | None] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(String(800))
    current_club_id: Mapped[int | None] = mapped_column(ForeignKey("clubs.id"))
    market_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    photo_url: Mapped[str | None] = mapped_column(String(500))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    transfers: Mapped[list["Transfer"]] = relationship(back_populates="player")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="player", cascade="all, delete-orphan")
    current_club: Mapped["Club | None"] = relationship(back_populates="current_players", foreign_keys=[current_club_id])


class Club(Base):
    __tablename__ = "clubs"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[int | None] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    country: Mapped[str | None] = mapped_column(String(80))
    league: Mapped[str | None] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(String(800))
    founded: Mapped[int | None] = mapped_column()
    stadium: Mapped[str | None] = mapped_column(String(160))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    outgoing_transfers: Mapped[list["Transfer"]] = relationship(
        back_populates="from_club", foreign_keys="Transfer.from_club_id"
    )
    incoming_transfers: Mapped[list["Transfer"]] = relationship(
        back_populates="to_club", foreign_keys="Transfer.to_club_id"
    )
    current_players: Mapped[list[Player]] = relationship(
        back_populates="current_club", foreign_keys="Player.current_club_id"
    )


class Transfer(Base):
    __tablename__ = "transfers"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(160), unique=True, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    from_club_id: Mapped[int | None] = mapped_column(ForeignKey("clubs.id"))
    to_club_id: Mapped[int | None] = mapped_column(ForeignKey("clubs.id"))
    transfer_date: Mapped[date | None] = mapped_column(Date)
    fee: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(8), default="EUR")
    transfer_type: Mapped[str | None] = mapped_column(String(80))
    source: Mapped[str] = mapped_column(String(40), default="manual")

    player: Mapped[Player] = relationship(back_populates="transfers")
    from_club: Mapped[Club | None] = relationship(back_populates="outgoing_transfers", foreign_keys=[from_club_id])
    to_club: Mapped[Club | None] = relationship(back_populates="incoming_transfers", foreign_keys=[to_club_id])


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "player_id", name="uq_favorite_user_player"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="favorites")
    player: Mapped[Player] = relationship(back_populates="favorites")


class ApiCache(Base):
    __tablename__ = "api_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    cache_key: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    endpoint: Mapped[str] = mapped_column(String(120))
    entity_type: Mapped[str] = mapped_column(String(40))
    data: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
