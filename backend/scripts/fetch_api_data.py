import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "api_data" / "api_football_raw.json"


def fetch_all() -> dict:
    settings = get_settings()
    if not settings.api_football_key:
        raise RuntimeError("API_FOOTBALL_KEY не задан в backend/.env")

    league_id = int(sys.argv[1]) if len(sys.argv) > 1 else 39
    season = int(sys.argv[2]) if len(sys.argv) > 2 else 2024
    max_requests = int(sys.argv[3]) if len(sys.argv) > 3 else 95
    include_transfers = len(sys.argv) < 5 or sys.argv[4].lower() != "players-only"
    target_spec = sys.argv[5] if len(sys.argv) > 5 else f"{league_id}:{season}"
    targets = [(int(item.split(":")[0]), int(item.split(":")[1])) for item in target_spec.split(",")]
    responses: list[dict] = []
    requests_used = 0
    stopped_reason = "completed"
    headers = {"x-apisports-key": settings.api_football_key}

    def request(client: httpx.Client, endpoint: str, params: dict) -> dict | None:
        nonlocal requests_used, stopped_reason
        if requests_used >= max_requests:
            stopped_reason = "local_request_budget_reached"
            return None
        response = client.get(f"{settings.api_football_base_url}{endpoint}", params=params)
        requests_used += 1
        if response.status_code == 429:
            stopped_reason = "api_rate_limit_reached"
            return None
        response.raise_for_status()
        data = response.json()
        responses.append({
            "cache_key": f"{endpoint}?{urlencode(sorted(params.items()))}",
            "endpoint": endpoint,
            "entity_type": endpoint.strip("/") or "root",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "params": params,
            "data": data,
        })
        return data

    with httpx.Client(timeout=30, headers=headers) as client:
        for target_league, target_season in targets:
            teams = request(client, "/teams", {"league": target_league, "season": target_season})
            if teams is None:
                break
            players_page = 1
            while True:
                players = request(client, "/players", {"league": target_league, "season": target_season, "page": players_page})
                if players is None:
                    break
                paging = players.get("paging", {})
                total_pages = int(paging.get("total", players_page))
                if players_page >= total_pages:
                    break
                players_page += 1
            if stopped_reason in {"api_rate_limit_reached", "local_request_budget_reached"}:
                break

            if include_transfers:
                player_ids = []
                for item in responses:
                    if item["endpoint"] != "/players":
                        continue
                    player_ids.extend(
                        row.get("player", {}).get("id")
                        for row in item["data"].get("response", [])
                        if row.get("player", {}).get("id")
                    )
                for external_id in dict.fromkeys(player_ids):
                    transfers = request(client, "/transfers", {"player": external_id})
                    if transfers is None:
                        break

    previous_responses = []
    if OUTPUT_PATH.exists():
        try:
            previous_responses = json.loads(OUTPUT_PATH.read_text(encoding="utf-8")).get("responses", [])
        except json.JSONDecodeError:
            previous_responses = []
    merged = {item["cache_key"]: item for item in previous_responses}
    merged.update({item["cache_key"]: item for item in responses})
    responses = list(merged.values())

    payload = {
        "source": "API-Football",
        "league_id": league_id,
        "season": season,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "request_count": requests_used,
        "stopped_reason": stopped_reason,
        "response_count": len(responses),
        "responses": responses,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = fetch_all()
    print(json.dumps({key: result[key] for key in ("league_id", "season", "request_count", "stopped_reason", "response_count")}, ensure_ascii=False))
