import httpx
from fastapi import HTTPException, status

from app.config import Settings


class FootballApiClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def check_connection(self) -> dict[str, str]:
        if not self.settings.api_football_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="API_FOOTBALL_KEY не задан в .env",
            )

        headers = {"x-apisports-key": self.settings.api_football_key}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{self.settings.api_football_base_url}/status",
                headers=headers,
            )
        if response.is_error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="API-Football вернул ошибку",
            )
        return {"status": "connected"}
