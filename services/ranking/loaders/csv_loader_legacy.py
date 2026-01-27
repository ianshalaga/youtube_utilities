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

from services.ranking.storage.session import SessionLocal
from services.ranking.storage.models import *
from services.ranking.loaders.base import DataLoader
from services.ranking.loaders.mappers.row_legacy_mapper import RowLegacyMapper
from services.ranking.loaders.mappers.event_type_mapper import resolve_event_type
from services.ranking.loaders.mappers.country_mapper import country_name_to_iso


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

            current_season = None
            current_event = None
            current_duel = None
            current_battle = None

            last_season_key = None
            last_event_key = None
            last_duel_key = None
            last_battle_key = None

            event_order = 0
            battle_order = 0

            for row_index, raw_row in enumerate(reader, start=1):
                row = RowLegacyMapper(raw_row)

                # @@@@ SEASON

                season_key = (row.season_name)

                if season_key != last_season_key:
                    current_season = self._get_or_create_season(session, row)
                    last_season_key = season_key
                    event_order = 0

                # @@@@ EVENT

                event_key = (
                    current_season.id,
                    row.event_name,
                    row.event_date,
                    row.region_name,
                    row.game_name,
                    row.game_version,
                    row.event_platform,
                    row.event_brackets,
                    row.event_playlist
                )

                if event_key != last_event_key:
                    event_order += 1
                    current_event = self._get_or_create_event(
                        session, row, current_season, event_order)
                    last_event_key = event_key
                    current_duel = None
                    last_duel_key = None

                # @@@@ DUEL

                duel_key = (
                    current_event.id,
                    row.duel_order,
                    row.duel_type,
                    row.duel_video
                )

                if duel_key != last_duel_key:
                    current_duel = self._get_or_create_duel(
                        session, current_event, row)
                    last_duel_key = duel_key
                    current_battle = None
                    last_battle_key = None
                    battle_order = 0

                # @@@@ BATTLE

                battle_key = (current_duel.id, row["combat_order"])

                if battle_key != last_battle_key:
                    battle_order += 1
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

    def _get_or_create_season(self, session, row):
        season = Season(
            name=row.season_name,
            start_date=self._parse_date(row.event_date)
        )
        session.add(season)
        return season

    def _get_or_create_country(self, session, name):
        country = session.query(Country).filter_by(name=name).one_or_none()
        if country is None:
            country = Country(iso_code=country_name_to_iso(name), name=name)
            session.add(country)
        return country

    def _get_or_create_player(self, session, nickname, country):
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

    def _get_or_create_event(self, session, row, season, event_order):
        event_type_name = resolve_event_type(row.event_name)

        event_type = self._get_or_create_simple(
            session, EventType, event_type_name)

        region = self._get_or_create_simple(
            session, Region, row.region_name)

        game = self._get_or_create_simple(session, Game, row.game_name)

        platform = self._get_or_create_simple(
            session, Platform, row.event_platform)

        game_version_platform = self._get_or_create_game_version_platform(
            session, game, platform, row.game_version)

        event = Event(
            name=row.event_name,
            event_date=self._parse_date(row.event_date),
            season_id=season.id,
            order=event_order,
            event_type_id=event_type.id,
            region_id=region.id,
            game_version_platform_id=game_version_platform.id,
            bracket_url=row.event_brackets,
            playlist_url=row.event_playlist,
        )

        session.add(event)
        return event

    def _get_or_create_duel(self, session, event, row):
        duel_type = self._get_or_create_simple(
            session, DuelType, row.duel_type
        )

        duel = Duel(
            event_id=event.id,
            duel_type_id=duel_type.id,
            order=int(row.duel_order),
            video_url=row.duel_video,
        )

        session.add(duel)

        # Countries
        p1_country = self._get_or_create_country(session, row.player_1_country)
        p2_country = self._get_or_create_country(session, row.player_2_country)

        # Participants
        p1 = self._get_or_create_player(session, row.player_1_name, p1_country)
        p2 = self._get_or_create_player(session, row.player_2_name, p2_country)

        session.add(DuelParticipant(duel_id=duel.id, player_id=p1.id))
        session.add(DuelParticipant(duel_id=duel.id, player_id=p2.id))

        if row.player_1_team is not None:
            p1_team = self._get_or_create_simple(
                session, Team, row.player_1_team)

            duel_team_p1 = DuelTeam(duel_id=duel.id, team_id=p1_team.id)
            session.add(duel_team_p1)

            session.add(DuelTeamMember(
                duel_team_id=duel_team_p1.id, player_id=p1.id))

        if row.player_2_team is not None:
            p2_team = self._get_or_create_simple(
                session, Team, row.player_2_team)

            duel_team_p2 = DuelTeam(duel_id=duel.id, team_id=p2_team.id)
            session.add(duel_team_p2)

            session.add(DuelTeamMember(
                duel_team_id=duel_team_p2.id, player_id=p2.id))

        return duel

    def _create_battle(self, session, duel, row):
        battle = Battle(
            duel_id=duel.id,
            order=int(row["combat_order"]),
        )
        session.add(battle)

        gv = (
            session.query(GameVersionPlatform)
            .join(Game)
            .filter(Game.name == row["game"], GameVersionPlatform.version == row["version"])
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
        '''
        Una entidad simple existe una sola vez por nombre.

        Evita duplicar entidades simples identificadas únicamente por name:
            Country
            Platform
            Game
            Region
            EventType

        Todas estas entidades cumplen el mismo patrón:
            Tienen un name
            El name es único a nivel conceptual
            No dependen de ningún otro campo para existir
        '''
        obj = session.query(model).filter_by(name=name).one_or_none()
        if obj is None:
            obj = model(name=name)
            session.add(obj)
        return obj

    def _get_or_create_game_version_platform(self, session, game, platform, version):
        '''
        Las versiones viven dentro de un juego, no son globales.
        '''
        gvp = (
            session.query(GameVersionPlatform)
            .filter_by(game_id=game.id, platform_id=platform.id, version=version)
            .one_or_none()
        )

        if gvp is None:
            gvp = GameVersionPlatform(
                game_id=game.id, platform_id=platform.id, version=version)
            session.add(gvp)
        return gvp

    @staticmethod
    def _parse_date(value: str | None):
        '''
        Las fechas son datos estructurales, no texto libre.
        '''
        if not value:
            return None

        value = value.strip()

        formats = (
            "%Y-%m-%d",     # YYYY-MM-DD (ISO 8601) Preferido
            "%Y/%m/%d",     # YYYY/MM/DD
            "%d/%m/%Y",     # DD/MM/YYYY
            "%d-%m-%Y",     # DD-MM-YYYY
        )

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

        raise ValueError(f"Formato de fecha no reconocido: {value}")
