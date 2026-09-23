from datetime import date, timedelta
from decimal import Decimal

import httpx
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Club, Favorite, Player, Transfer


DEMO_PLAYERS = [
    {"name": "Kylian Mbappe", "birth_date": date(1998, 12, 20), "nationality": "France", "position": "Forward"},
    {"name": "Jude Bellingham", "birth_date": date(2003, 6, 29), "nationality": "England", "position": "Midfielder"},
    {"name": "Erling Haaland", "birth_date": date(2000, 7, 21), "nationality": "Norway", "position": "Forward"},
    {"name": "Declan Rice", "birth_date": date(1999, 1, 14), "nationality": "England", "position": "Midfielder"},
    {"name": "Moises Caicedo", "birth_date": date(2001, 11, 2), "nationality": "Ecuador", "position": "Midfielder"},
    {"name": "Enzo Fernandez", "birth_date": date(2001, 1, 17), "nationality": "Argentina", "position": "Midfielder"},
    {"name": "Victor Osimhen", "birth_date": date(1998, 12, 29), "nationality": "Nigeria", "position": "Forward"},
    {"name": "Alexander Isak", "birth_date": date(1999, 9, 21), "nationality": "Sweden", "position": "Forward"},
]

DEMO_CLUBS = [
    {"name": "Real Madrid", "country": "Spain", "league": "La Liga"},
    {"name": "Paris Saint-Germain", "country": "France", "league": "Ligue 1"},
    {"name": "Borussia Dortmund", "country": "Germany", "league": "Bundesliga"},
    {"name": "Manchester City", "country": "England", "league": "Premier League"},
    {"name": "West Ham United", "country": "England", "league": "Premier League"},
    {"name": "Arsenal", "country": "England", "league": "Premier League"},
    {"name": "Brighton", "country": "England", "league": "Premier League"},
    {"name": "Chelsea", "country": "England", "league": "Premier League"},
    {"name": "Benfica", "country": "Portugal", "league": "Primeira Liga"},
    {"name": "Napoli", "country": "Italy", "league": "Serie A"},
    {"name": "Newcastle United", "country": "England", "league": "Premier League"},
    {"name": "Real Sociedad", "country": "Spain", "league": "La Liga"},
]

DEMO_TRANSFERS = [
    ("Kylian Mbappe", "Paris Saint-Germain", "Real Madrid", date(2024, 7, 1), Decimal("0"), "Free transfer"),
    ("Jude Bellingham", "Borussia Dortmund", "Real Madrid", date(2023, 6, 14), Decimal("103000000"), "Permanent"),
    ("Erling Haaland", "Borussia Dortmund", "Manchester City", date(2022, 7, 1), Decimal("60000000"), "Permanent"),
    ("Declan Rice", "West Ham United", "Arsenal", date(2023, 7, 15), Decimal("116000000"), "Permanent"),
    ("Moises Caicedo", "Brighton", "Chelsea", date(2023, 8, 14), Decimal("116000000"), "Permanent"),
    ("Enzo Fernandez", "Benfica", "Chelsea", date(2023, 2, 1), Decimal("121000000"), "Permanent"),
    ("Victor Osimhen", "Napoli", "Chelsea", date(2025, 9, 1), Decimal("69000000"), "Permanent"),
    ("Alexander Isak", "Real Sociedad", "Newcastle United", date(2022, 8, 26), Decimal("70000000"), "Permanent"),
]

DEMO_PHOTO_IDS = {
    "Kylian Mbappe": 278,
    "Jude Bellingham": 129,
    "Erling Haaland": 1100,
    "Declan Rice": 865,
}

DEMO_CURRENT_CLUBS = {
    "Kylian Mbappe": "Real Madrid",
    "Jude Bellingham": "Real Madrid",
    "Erling Haaland": "Manchester City",
    "Declan Rice": "Arsenal",
    "Moises Caicedo": "Chelsea",
    "Enzo Fernandez": "Chelsea",
    "Victor Osimhen": "Chelsea",
    "Alexander Isak": "Newcastle United",
}

DEMO_PLAYER_DESCRIPTIONS = {
    "Kylian Mbappe": "Французский нападающий с высокой скоростью, завершением атак и опытом выступлений на высшем уровне.",
    "Jude Bellingham": "Универсальный английский полузащитник, совмещающий продвижение мяча, прессинг и голевые подключения.",
    "Erling Haaland": "Мощный норвежский форвард, специализирующийся на игре в штрафной и завершении быстрых атак.",
    "Declan Rice": "Английский центральный полузащитник с сильным отбором, выносливостью и качественным первым пасом.",
    "Moises Caicedo": "Эквадорский опорный полузащитник, эффективно разрушающий атаки и работающий между линиями.",
    "Enzo Fernandez": "Аргентинский полузащитник с развитым видением поля, длинной передачей и контролем темпа.",
    "Victor Osimhen": "Нигерийский нападающий, опасный в рывках за спину защитникам и игре на втором этаже.",
    "Alexander Isak": "Шведский форвард с хорошей техникой, движением в штрафной и умением играть в связке.",
}

CLUB_DETAILS = {
    "Real Madrid": (1902, "Santiago Bernabeu", "Мадридский клуб с богатой историей и одной из самых успешных европейских традиций."),
    "Paris Saint-Germain": (1970, "Parc des Princes", "Парижский клуб, известный сильной академией и международными звездами."),
    "Borussia Dortmund": (1909, "Signal Iduna Park", "Немецкий клуб с яркой атмосферой, развитой молодежной системой и атакующим стилем."),
    "Manchester City": (1880, "Etihad Stadium", "Английский клуб с современной инфраструктурой и контролем мяча как основой игры."),
    "West Ham United": (1895, "London Stadium", "Лондонский клуб с историей развития английских полузащитников и сильной поддержкой."),
    "Arsenal": (1886, "Emirates Stadium", "Лондонская команда с узнаваемой школой комбинационного футбола и развитой академией."),
    "Brighton": (1901, "American Express Stadium", "Клуб, который сочетает аналитический подход, скаутинг и развитие молодых игроков."),
    "Chelsea": (1905, "Stamford Bridge", "Лондонский клуб с международной селекцией, сильной академией и богатой коллекцией трофеев."),
    "Benfica": (1904, "Estadio da Luz", "Португальский клуб, известный академией и подготовкой игроков для европейского рынка."),
    "Napoli": (1926, "Stadio Diego Armando Maradona", "Неаполитанский клуб с эмоциональной поддержкой и выразительной атакующей культурой."),
    "Newcastle United": (1892, "St James Park", "Исторический английский клуб с большой аудиторией и амбициозным проектом развития."),
    "Real Sociedad": (1909, "Reale Arena", "Баскский клуб с сильной школой, локальной идентичностью и вниманием к техничным игрокам."),
}

DEMO_LOGO_IDS = {
    "Real Madrid": 541,
    "Paris Saint-Germain": 85,
    "Borussia Dortmund": 165,
    "Manchester City": 50,
    "West Ham United": 48,
    "Arsenal": 42,
    "Brighton": 51,
    "Chelsea": 49,
    "Benfica": 211,
    "Napoli": 492,
    "Newcastle United": 34,
    "Real Sociedad": 548,
}


class DemoSeedService:
    def __init__(self, settings: Settings, db: Session) -> None:
        self.settings = settings
        self.db = db
        self.requests_used = 0

    async def seed(self) -> dict[str, int | str]:
        self._clear_catalog()
        clubs = {club["name"]: Club(**club) for club in DEMO_CLUBS}
        for name, (founded, stadium, description) in CLUB_DETAILS.items():
            clubs[name].founded = founded
            clubs[name].stadium = stadium
            clubs[name].description = description
        self.db.add_all(list(clubs.values()))
        self.db.flush()
        for name, external_id in DEMO_LOGO_IDS.items():
            clubs[name].external_id = external_id
            clubs[name].logo_url = f"https://media.api-sports.io/football/teams/{external_id}.png"

        players = {}
        club_values = list(clubs.values())
        for index, player_data in enumerate(DEMO_PLAYERS):
            player_name = player_data["name"]
            current_club = clubs[DEMO_CURRENT_CLUBS[player_name]]
            player = Player(**player_data, description=DEMO_PLAYER_DESCRIPTIONS[player_name], current_club_id=current_club.id, market_value=Decimal("85000000"))
            players[player_name] = player
            self.db.add(player)
        for index in range(1, 993):
            current_club = club_values[index % len(club_values)]
            previous_club = club_values[(index + 3) % len(club_values)]
            player_name = f"Academy Player {index:04d}"
            player = Player(
                name=player_name,
                birth_date=date(1988 + (index % 15), 1 + (index % 12), 1 + (index % 27)),
                nationality=("England", "Spain", "France", "Brazil", "Germany", "Argentina")[index % 6],
                position=("Forward", "Midfielder", "Defender", "Goalkeeper")[index % 4],
                description=f"Профиль учебной базы: игрок академического типа, развивающийся в позиции {('Forward', 'Midfielder', 'Defender', 'Goalkeeper')[index % 4]}.",
                current_club_id=current_club.id,
                market_value=Decimal(str(500000 + (index % 80) * 250000)),
            )
            players[player_name] = player
            self.db.add(player)
        self.db.flush()

        for player_name, from_name, to_name, transfer_date, fee, transfer_type in DEMO_TRANSFERS:
            self.db.add(
                Transfer(
                    external_id=f"demo:{player_name}:{transfer_date.isoformat()}",
                    player_id=players[player_name].id,
                    from_club_id=clubs[from_name].id,
                    to_club_id=clubs[to_name].id,
                    transfer_date=transfer_date,
                    fee=fee,
                    currency="EUR",
                    transfer_type=transfer_type,
                    source="demo-dataset",
                )
            )
        for index in range(1, 993):
            player_name = f"Academy Player {index:04d}"
            current_club = club_values[index % len(club_values)]
            previous_club = club_values[(index + 3) % len(club_values)]
            self.db.add(Transfer(
                external_id=f"demo:academy:{index}",
                player_id=players[player_name].id,
                from_club_id=previous_club.id,
                to_club_id=current_club.id,
                transfer_date=date(2020, 1, 1) + timedelta(days=index * 2),
                fee=Decimal(str(500000 + (index % 80) * 250000)),
                currency="EUR",
                transfer_type="Permanent",
                source="demo-dataset",
            ))
        self.db.commit()

        photos_found = await self._enrich_photos(players)
        self.db.commit()
        return {
            "status": "completed",
            "players": len(players),
            "clubs": len(clubs),
            "transfers": len(players),
            "photos_found": photos_found,
            "requests_used": self.requests_used,
        }

    def _clear_catalog(self) -> None:
        self.db.execute(delete(Favorite))
        self.db.execute(delete(Transfer))
        self.db.execute(delete(Player))
        self.db.execute(delete(Club))
        self.db.flush()

    async def _enrich_photos(self, players: dict[str, Player]) -> int:
        photos_found = 0
        for name, external_id in DEMO_PHOTO_IDS.items():
            player = players.get(name)
            if player:
                player.photo_url = f"https://media.api-sports.io/football/players/{external_id}.png"
                photos_found += 1

        if not self.settings.api_football_key:
            return photos_found
        headers = {"x-apisports-key": self.settings.api_football_key}
        async with httpx.AsyncClient(timeout=20, headers=headers) as client:
            for player in players.values():
                try:
                    response = await client.get(
                        f"{self.settings.api_football_base_url}/players",
                        params={"league": 39, "season": 2024, "search": player.name},
                    )
                except httpx.HTTPError:
                    continue
                self.requests_used += 1
                if response.status_code == 429:
                    break
                if response.is_error:
                    continue
                rows = response.json().get("response", [])
                if rows:
                    photo = (rows[0].get("player") or rows[0]).get("photo")
                    if photo:
                        had_photo = bool(player.photo_url)
                        player.photo_url = photo
                        if not had_photo:
                            photos_found += 1
        return photos_found


def remove_generated_players(db: Session) -> int:
    generated = list(db.scalars(select(Player).where(Player.name.like("Academy Player %"))).all())
    if not generated:
        return 0
    player_ids = [player.id for player in generated]
    db.execute(delete(Transfer).where(Transfer.player_id.in_(player_ids)))
    db.execute(delete(Player).where(Player.id.in_(player_ids)))
    db.commit()
    return len(generated)


def remove_curated_demo_data(db: Session) -> dict[str, int]:
    demo_players = list(db.scalars(select(Player).where(Player.external_id.is_(None))).all())
    demo_player_ids = [player.id for player in demo_players]
    demo_transfers = list(db.scalars(select(Transfer).where(Transfer.source == "demo-dataset")).all())
    if demo_player_ids:
        db.execute(delete(Transfer).where(Transfer.player_id.in_(demo_player_ids)))
        db.execute(delete(Player).where(Player.id.in_(demo_player_ids)))
    if demo_transfers:
        db.execute(delete(Transfer).where(Transfer.source == "demo-dataset"))
    db.commit()
    return {"removed_players": len(demo_players), "removed_transfers": len(demo_transfers)}
