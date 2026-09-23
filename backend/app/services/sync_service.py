from datetime import date
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

import httpx
import re
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import ApiCache, Club, Player, Transfer
from app.schemas.sync import SyncRequest, SyncResult


class FootballSyncService:
    def __init__(self, settings: Settings, db: Session) -> None:
        self.settings = settings
        self.db = db
        self.requests_used = 0

    async def sync(self, payload: SyncRequest) -> SyncResult:
        if not self.settings.api_football_key:
            raise ValueError("API_FOOTBALL_KEY не задан в .env")

        headers = {"x-apisports-key": self.settings.api_football_key}
        async with httpx.AsyncClient(timeout=20, headers=headers) as client:
            teams_data = await self._get(client, "/teams", {"league": payload.league_id, "season": payload.season})
            clubs_created, clubs_updated = self._upsert_teams(teams_data.get("response", []), payload.league_id)
            self.db.commit()

            players_created = players_updated = 0
            for page in range(1, payload.player_pages + 1):
                players_data = await self._get(
                    client,
                    "/players",
                    {"league": payload.league_id, "season": payload.season, "page": page},
                )
                created, updated = self._upsert_players(players_data.get("response", []))
                players_created += created
                players_updated += updated
                self.db.commit()

            # Keep the real catalog even if the daily quota ends during history import.
            self.db.commit()

            transfers_created = transfers_updated = 0
            for player_id in payload.player_ids:
                transfers_data = await self._get(client, "/transfers", {"player": player_id})
                created, updated = self._upsert_transfers(transfers_data.get("response", []))
                transfers_created += created
                transfers_updated += updated
                self.db.commit()

        self.db.commit()
        return SyncResult(
            status="completed",
            players_created=players_created,
            players_updated=players_updated,
            clubs_created=clubs_created,
            clubs_updated=clubs_updated,
            transfers_created=transfers_created,
            transfers_updated=transfers_updated,
            requests_used=self.requests_used,
        )

    def reprocess_cached_data(self) -> dict[str, int]:
        players_created = players_updated = 0
        clubs_created = clubs_updated = 0
        transfers_created = transfers_updated = 0
        for cached in self.db.scalars(select(ApiCache).order_by(ApiCache.id)).all():
            rows = cached.data.get("response", [])
            if cached.endpoint == "/teams":
                current_created, current_updated = self._upsert_teams(rows, 0)
                clubs_created += current_created
                clubs_updated += current_updated
            elif cached.endpoint == "/players":
                current_created, current_updated = self._upsert_players(rows)
                players_created += current_created
                players_updated += current_updated
            elif cached.endpoint == "/transfers":
                current_created, current_updated = self._upsert_transfers(rows)
                transfers_created += current_created
                transfers_updated += current_updated
        self.db.commit()
        return {
            "players_created": players_created,
            "players_updated": players_updated,
            "clubs_created": clubs_created,
            "clubs_updated": clubs_updated,
            "transfers_created": transfers_created,
            "transfers_updated": transfers_updated,
        }

    def clear_unverified_catalog_fields(self) -> None:
        self.db.execute(update(Player).values(description=None, market_value=None))
        self.db.execute(update(Club).values(description=None, founded=None, stadium=None))
        self.db.commit()

    def reprocess_cached_transfers(self) -> tuple[int, int]:
        result = self.reprocess_cached_data()
        return result["transfers_created"], result["transfers_updated"]

    async def _get(self, client: httpx.AsyncClient, path: str, params: dict[str, int]) -> dict:
        response = await client.get(f"{self.settings.api_football_base_url}{path}", params=params)
        self.requests_used += 1
        response.raise_for_status()
        data = response.json()
        cache_key = f"{path}?{urlencode(sorted(params.items()))}"
        cached = self.db.scalar(select(ApiCache).where(ApiCache.cache_key == cache_key))
        values = {"cache_key": cache_key, "endpoint": path, "entity_type": path.strip("/") or "root", "data": data}
        if cached:
            cached.data = data
            cached.endpoint = path
        else:
            self.db.add(ApiCache(**values))
        return data

    def _upsert_teams(self, rows: list[dict], league_id: int) -> tuple[int, int]:
        created = updated = 0
        seen_external_ids: set[int] = set()
        for row in rows:
            data = row.get("team", row)
            external_id = data.get("id")
            if not external_id:
                continue
            if external_id in seen_external_ids:
                continue
            seen_external_ids.add(external_id)
            club = self.db.scalar(select(Club).where(Club.external_id == external_id))
            values = {
                "name": data.get("name") or f"Club {external_id}",
                "country": data.get("country"),
                "league": str(league_id) if league_id else None,
                "founded": data.get("founded"),
                "stadium": (row.get("venue") or {}).get("name"),
                "logo_url": data.get("logo"),
            }
            if club:
                for key, value in values.items():
                    setattr(club, key, value)
                updated += 1
            else:
                self.db.add(Club(external_id=external_id, **values))
                self.db.flush()
                created += 1
        return created, updated

    def reprocess_cached_data(self) -> dict[str, int]:
        teams_created = teams_updated = players_created = players_updated = 0
        transfers_created = transfers_updated = 0
        cached_rows = self.db.scalars(select(ApiCache).order_by(ApiCache.id)).all()
        for cached in cached_rows:
            rows = cached.data.get("response", [])
            if cached.endpoint == "/teams":
                created, updated = self._upsert_teams(rows, 0)
                teams_created += created
                teams_updated += updated
            elif cached.endpoint == "/players":
                created, updated = self._upsert_players(rows)
                players_created += created
                players_updated += updated
            elif cached.endpoint == "/transfers":
                created, updated = self._upsert_transfers(rows)
                transfers_created += created
                transfers_updated += updated
        self.db.commit()
        return {
            "teams_created": teams_created,
            "teams_updated": teams_updated,
            "players_created": players_created,
            "players_updated": players_updated,
            "transfers_created": transfers_created,
            "transfers_updated": transfers_updated,
        }

    def _upsert_players(self, rows: list[dict]) -> tuple[int, int]:
        created = updated = 0
        for row in rows:
            data = row.get("player", row)
            external_id = data.get("id")
            if not external_id:
                continue
            player = self.db.scalar(select(Player).where(Player.external_id == external_id))
            birth_date = self._parse_date((data.get("birth") or {}).get("date"))
            statistics = row.get("statistics") or []
            team_data = (statistics[0].get("team") if statistics else None) or {}
            current_club = self._find_or_create_club(team_data)
            values = {
                "name": data.get("name") or "Unknown player",
                "birth_date": birth_date,
                "nationality": data.get("nationality"),
                "position": data.get("position"),
                "photo_url": data.get("photo"),
                "current_club_id": current_club.id if current_club else None,
                "description": None,
                "market_value": None,
            }
            if player:
                for key, value in values.items():
                    setattr(player, key, value)
                updated += 1
            else:
                self.db.add(Player(external_id=external_id, **values))
                created += 1
        return created, updated

    def _upsert_transfers(self, rows: list[dict]) -> tuple[int, int]:
        created = updated = 0
        for row in rows:
            player_data = row.get("player", {})
            external_player_id = player_data.get("id")
            player = self.db.scalar(select(Player).where(Player.external_id == external_player_id))
            if not player:
                continue
            for item in row.get("transfers", []):
                transfer_date = self._parse_date(item.get("date"))
                teams = item.get("teams") or {}
                from_club = self._find_or_create_club(teams.get("out"))
                to_club = self._find_or_create_club(teams.get("in"))
                external_id = f"{external_player_id}:{item.get('date')}:{item.get('type')}:{from_club.id if from_club else 0}:{to_club.id if to_club else 0}"
                transfer = self.db.scalar(select(Transfer).where(Transfer.external_id == external_id))
                values = {
                    "player_id": player.id,
                    "from_club_id": from_club.id if from_club else None,
                    "to_club_id": to_club.id if to_club else None,
                    "transfer_date": transfer_date,
                    "fee": self._parse_fee(item.get("type")),
                    "transfer_type": item.get("type"),
                    "source": "api-football",
                }
                if transfer:
                    for key, value in values.items():
                        setattr(transfer, key, value)
                    updated += 1
                else:
                    self.db.add(Transfer(external_id=external_id, **values))
                    created += 1
        return created, updated

    @staticmethod
    def _parse_fee(value: str | None) -> Decimal | None:
        if not value:
            return None
        match = re.search(r"€\s*([\d.,]+)\s*([KMB])?", value, re.IGNORECASE)
        if not match:
            return Decimal("0") if "free" in value.lower() else None
        amount = Decimal(match.group(1).replace(",", "."))
        multiplier = {"K": Decimal("1000"), "M": Decimal("1000000"), "B": Decimal("1000000000")}
        return amount * multiplier.get((match.group(2) or "").upper(), Decimal("1"))

    def _find_or_create_club(self, data: dict | None) -> Club | None:
        if not data or not data.get("id"):
            return None
        club = self.db.scalar(select(Club).where(Club.external_id == data["id"]))
        if club:
            return club
        club = Club(
            external_id=data["id"],
            name=data.get("name") or f"Club {data['id']}",
            logo_url=data.get("logo"),
        )
        self.db.add(club)
        self.db.flush()
        return club

    def _find_or_create_club(self, data: dict | None) -> Club | None:
        if not data or not data.get("id"):
            return None
        club = self.db.scalar(select(Club).where(Club.external_id == data["id"]))
        if club:
            return club
        club = Club(external_id=data["id"], name=data.get("name") or f"Club {data['id']}", logo_url=data.get("logo"))
        self.db.add(club)
        self.db.flush()
        return club

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        if not value:
            return None
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
