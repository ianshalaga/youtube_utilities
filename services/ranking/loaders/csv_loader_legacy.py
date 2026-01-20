"""
CSV Loader Legacy

Carga histórica de datos desde el CSV legacy original.
La carga es ATÓMICA: o se carga todo o no se carga nada.

Este loader:
- NO persiste datos calculados
- Respeta orden temporal
- Crea entidades si no existen
- Realiza rollback completo ante cualquier error
"""

import csv
from pathlib import Path
from datetime import datetime

from services.ranking.loaders.base import DataLoader
from services.ranking.storage.session import SessionLocal
from services.ranking.storage.models import *
# from services.ranking.storage.models import (
#     Country,
#     Player,
#     PlayerAlias,
#     Platform,
#     Game,
#     GameVersion,
#     Season,
#     Event,
#     Duel,
#     DuelParticipant,
#     Battle,
#     BattleParticipant,
#     Round,
#     RoundResult,
#     CharacterIdentity,
#     GameCharacter,
# )


class CSVLoaderLegacy(DataLoader):
    def __init__(self, csv_path: Path):
        if not csv_path.exists():
            raise FileNotFoundError(csv_path)
        self._csv_path = csv_path

    # ──────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────

    def load(self) -> None:
        """
        Ejecuta la carga completa del CSV legacy.

        La operación es transaccional:
        - commit si todo es válido
        - rollback si ocurre cualquier error
        """
        session = SessionLocal()

        try:
            with session.begin():
                self._load_csv(session)

            print("Carga legacy completada correctamente.")

        except Exception:
            print("Error durante la carga legacy. Rollback aplicado.")
            raise

        finally:
            session.close()

    # ──────────────────────────────────────────────
    # Core loader
    # ──────────────────────────────────────────────

    def _load_csv(self, session):
        with self._csv_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)

            current_event = None
            current_duel = None
            current_battle = None

            last_event_key = None
            last_duel_key = None
            last_battle_key = None

            for row_index, row in enumerate(reader, start=1):
                # ───────────────────────────────────
                # EVENT
                # ───────────────────────────────────
                event_key = (
                    row["event_name"],
                    row["platform"],
                    row["game"],
                    row["version"],
                )

                if event_key != last_event_key:
                    current_event = self._get_or_create_event(session, row)
                    last_event_key = event_key
                    current_duel = None
                    last_duel_key = None

                # ───────────────────────────────────
                # DUEL
                # ───────────────────────────────────
                duel_key = (current_event.id, row["duel_order"])

                if duel_key != last_duel_key:
                    current_duel = self._create_duel(
                        session, current_event, row)
                    last_duel_key = duel_key
                    current_battle = None
                    last_battle_key = None

                # ───────────────────────────────────
                # BATTLE
                # ───────────────────────────────────
                battle_key = (current_duel.id, row["combat_order"])

                if battle_key != last_battle_key:
                    current_battle = self._create_battle(
                        session, current_duel, row)
                    last_battle_key = battle_key

                # ───────────────────────────────────
                # ROUNDS
                # ───────────────────────────────────
                self._create_rounds(session, current_battle, row)

    # ──────────────────────────────────────────────
    # Entity creation helpers
    # ──────────────────────────────────────────────

    def _get_or_create_country(self, session, code, name):
        country = session.query(Country).filter_by(code=code).one_or_none()
        if country is None:
            country = Country(code=code, name=name)
            session.add(country)
        return country

    def _get_or_create_player(self, session, nickname, country_code):
        country = session.query(Country).filter_by(
            code=country_code).one_or_none()
        if country is None:
            raise ValueError(f"Country not found: {country_code}")

        player = session.query(Player).filter_by(
            nickname=nickname).one_or_none()
        if player is None:
            player = Player(nickname=nickname, country_id=country.id)
            session.add(player)
        return player

    def _get_or_create_character(self, session, name, game_version):
        identity = (
            session.query(CharacterIdentity)
            .filter_by(name=name, franchise=game_version.game.name)
            .one_or_none()
        )

        if identity is None:
            identity = CharacterIdentity(
                name=name, franchise=game_version.game.name)
            session.add(identity)

        game_character = (
            session.query(GameCharacter)
            .filter_by(
                character_identity_id=identity.id,
                game_version_id=game_version.id,
            )
            .one_or_none()
        )

        if game_character is None:
            game_character = GameCharacter(
                character_identity_id=identity.id,
                game_version_id=game_version.id,
            )
            session.add(game_character)

        return game_character

    def _get_or_create_event(self, session, row):
        platform = self._get_or_create_simple(
            session, Platform, row["platform"])
        game = self._get_or_create_simple(session, Game, row["game"])
        game_version = self._get_or_create_game_version(
            session, game, row["version"])

        event = Event(
            name=row["event_name"],
            platform_id=platform.id,
            game_version_id=game_version.id,
            bracket_url=row.get("event_bracket"),
            playlist_url=row.get("event_playlist"),
            event_type=row.get("event_type"),
            event_date=self._parse_date(row.get("event_date")),
        )
        session.add(event)
        return event

    def _create_duel(self, session, event, row):
        duel = Duel(
            event_id=event.id,
            order=int(row["duel_order"]),
            video_url=row.get("duel_video"),
        )
        session.add(duel)

        # participants
        p1 = self._get_or_create_player(
            session, row["player_1"], row["p1_country"]
        )
        p2 = self._get_or_create_player(
            session, row["player_2"], row["p2_country"]
        )

        session.add(DuelParticipant(duel_id=duel.id, player_id=p1.id))
        session.add(DuelParticipant(duel_id=duel.id, player_id=p2.id))

        return duel

    def _create_battle(self, session, duel, row):
        battle = Battle(
            duel_id=duel.id,
            order=int(row["combat_order"]),
        )
        session.add(battle)

        gv = (
            session.query(GameVersion)
            .join(Game)
            .filter(Game.name == row["game"], GameVersion.version == row["version"])
            .one()
        )

        p1 = session.query(Player).filter_by(nickname=row["player_1"]).one()
        p2 = session.query(Player).filter_by(nickname=row["player_2"]).one()

        c1 = self._get_or_create_character(session, row["character_1"], gv)
        c2 = self._get_or_create_character(session, row["character_2"], gv)

        session.add(BattleParticipant(battle_id=battle.id,
                    player_id=p1.id, game_character_id=c1.id))
        session.add(BattleParticipant(battle_id=battle.id,
                    player_id=p2.id, game_character_id=c2.id))

        return battle

    def _create_rounds(self, session, battle, row):
        for i in range(1, 6):
            r1 = row.get(f"p1_r{i}")
            r2 = row.get(f"p2_r{i}")

            if not r1 or not r2:
                continue

            round_ = Round(battle_id=battle.id, order=i)
            session.add(round_)

            p1 = session.query(Player).filter_by(
                nickname=row["player_1"]).one()
            p2 = session.query(Player).filter_by(
                nickname=row["player_2"]).one()

            session.add(RoundResult(round_id=round_.id,
                        player_id=p1.id, result_code=r1))
            session.add(RoundResult(round_id=round_.id,
                        player_id=p2.id, result_code=r2))

    # ──────────────────────────────────────────────
    # Utilities
    # ──────────────────────────────────────────────

    def _get_or_create_simple(self, session, model, name):
        obj = session.query(model).filter_by(name=name).one_or_none()
        if obj is None:
            obj = model(name=name)
            session.add(obj)
        return obj

    def _get_or_create_game_version(self, session, game, version):
        gv = (
            session.query(GameVersion)
            .filter_by(game_id=game.id, version=version)
            .one_or_none()
        )
        if gv is None:
            gv = GameVersion(game_id=game.id, version=version)
            session.add(gv)
        return gv

    @staticmethod
    def _parse_date(value):
        if not value:
            return None
        return datetime.strptime(value, "%Y-%m-%d").date()
