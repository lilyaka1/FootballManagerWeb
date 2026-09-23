from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PlayerBase(BaseModel):
    name: str
    birth_date: date | None = None
    nationality: str | None = None
    position: str | None = None
    description: str | None = None
    current_club_id: int | None = None
    current_club_name: str | None = None
    market_value: Decimal | None = None
    photo_url: str | None = None


class PlayerCreate(PlayerBase):
    external_id: int | None = None


class PlayerResponse(PlayerBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    external_id: int | None


class ClubBase(BaseModel):
    name: str
    country: str | None = None
    league: str | None = None
    description: str | None = None
    founded: int | None = None
    stadium: str | None = None
    logo_url: str | None = None


class ClubCreate(ClubBase):
    external_id: int | None = None


class ClubResponse(ClubBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    external_id: int | None


class TransferCreate(BaseModel):
    player_id: int
    from_club_id: int | None = None
    to_club_id: int | None = None
    transfer_date: date | None = None
    fee: Decimal | None = None
    currency: str = "EUR"
    transfer_type: str | None = None
    external_id: str | None = None


class TransferResponse(TransferCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source: str
    player_name: str | None = None
    from_club_name: str | None = None
    to_club_name: str | None = None


class PlayerDetailsResponse(PlayerResponse):
    transfers: list[TransferResponse] = Field(default_factory=list)


class ClubDetailsResponse(ClubResponse):
    current_players: list[PlayerResponse] = Field(default_factory=list)
    incoming_transfers: list[TransferResponse] = Field(default_factory=list)
    outgoing_transfers: list[TransferResponse] = Field(default_factory=list)


class SummaryResponse(BaseModel):
    players_count: int
    clubs_count: int
    transfers_count: int
    total_fee: Decimal
