from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.catalog import PlayerResponse


class FavoriteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_id: int
    created_at: datetime
    player: PlayerResponse
