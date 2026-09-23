from pydantic import BaseModel, Field


class SyncRequest(BaseModel):
    league_id: int = Field(gt=0)
    season: int = Field(ge=2000, le=2100)
    player_ids: list[int] = Field(default_factory=list, max_length=45)
    player_pages: int = Field(default=1, ge=1, le=50)


class SyncResult(BaseModel):
    status: str
    players_created: int = 0
    players_updated: int = 0
    clubs_created: int = 0
    clubs_updated: int = 0
    transfers_created: int = 0
    transfers_updated: int = 0
    requests_used: int = 0
