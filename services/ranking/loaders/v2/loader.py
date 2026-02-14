"""
CSV Loader V2

Carga incremental e idempotente desde CSV moderno (1 round por fila).
El CSV puede re-ejecutarse completo sin duplicar datos.
"""

import csv
from pathlib import Path
from sqlalchemy.orm import Session
from datetime import datetime

from services.ranking.storage.session import SessionLocal
from services.ranking.loaders.base import DataLoader
from services.ranking.storage.base import Base
from services.ranking.loaders.v2.row_v2_mapper import RowV2Mapper
from services.ranking.loaders.mappers.country_mapper import country_name_to_iso

from services.ranking.storage.models import (
    Season, Event, Duel, Battle, Round,
    Player, Country, Team, DuelTeam, DuelTeamMember,
    BattleParticipant, RoundResult,
    Game, Platform, GameVersionPlatform,
    GameCharacter, CharacterIdentity,
    EventType, Region, DuelType, Stage,
)


class CSVLoaderV2(DataLoader):

    def __init__(self, csv_path: Path):
        if not csv_path.exists():
            raise FileNotFoundError(csv_path)
        self._csv_path = csv_path
        self._country_cache: dict[str, Country] = {}

    # ──────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────

    def load(self) -> None:
        session = SessionLocal()
        try:
            with session.begin():
                self._load_csv(session)
            print("Carga v2 completada correctamente.")
        except Exception:
            print("Error durante la carga v2. Rollback aplicado.")
            raise
        finally:
            session.close()

    # ──────────────────────────────────────────────
    # Core loader
    # ──────────────────────────────────────────────

    def _load_csv(self, session: Session):
        with self._csv_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for raw_row in reader:
                row = RowV2Mapper(raw_row)

                # ───── Season
                season = self._get_or_create_season(session, row)

                # ───── Event
                event, gvp = self._get_or_create_event(session, row, season)

                # ───── Duel
                duel, duel_teams, p1, p2 = self._get_or_create_duel(
                    session, row, event
                )

                # ───── Battle
                battle = self._get_or_create_battle(
                    session, row, duel, duel_teams, gvp, p1, p2
                )

                # ───── Round
                self._get_or_create_round(
                    session, row, battle, p1, p2
                )

    # ──────────────────────────────────────────────
    # Entity creation
    # ──────────────────────────────────────────────

    def _get_or_create_season(self, session, row):
        season = session.query(Season).filter_by(
            name=row.season_name
        ).one_or_none()

        if season is None:
            season = Season(
                name=row.season_name,
                start_date=self._parse_date(row.event_date)
            )
            session.add(season)

        return season

    def _get_or_create_event(self, session, row, season):
        event_type = self._get_or_create_simple(
            session, EventType, row.event_type
        )
        region = self._get_or_create_simple(
            session, Region, row.region_name
        )
        game = self._get_or_create_simple(session, Game, row.game_name)
        platform = self._get_or_create_simple(
            session, Platform, row.platform_name)

        gvp = self._get_or_create_game_version_platform(
            session, game, platform, row.game_version
        )

        event = (
            session.query(Event)
            .filter_by(
                name=row.event_name,
                season_id=season.id,
            )
            .one_or_none()
        )

        if event is None:
            event = Event(
                name=row.event_name,
                event_date=self._parse_date(row.event_date),
                season=season,
                event_type=event_type,
                region=region,
                game_version_platform=gvp,
            )
            session.add(event)

        return event, gvp

    def _get_or_create_duel(self, session, row, event):
        duel_type = self._get_or_create_simple(
            session, DuelType, row.duel_type
        )

        duel = (
            session.query(Duel)
            .filter_by(
                event_id=event.id,
                order=int(row.duel_order),
            )
            .one_or_none()
        )

        if duel is None:
            duel = Duel(
                event=event,
                duel_type=duel_type,
                order=int(row.duel_order),
                video_url=row.duel_video,
            )
            session.add(duel)

        # Players & countries
        p1_country = self._get_or_create_country(
            session, country_name_to_iso(
                row.player_1_country), row.player_1_country
        )
        p2_country = self._get_or_create_country(
            session, country_name_to_iso(
                row.player_2_country), row.player_2_country
        )

        p1 = self._get_or_create_player(session, row.player_1_name, p1_country)
        p2 = self._get_or_create_player(session, row.player_2_name, p2_country)

        duel_teams = {}
        duel_teams["p1"] = self._attach_team(
            session, duel, p1, row.player_1_team)
        duel_teams["p2"] = self._attach_team(
            session, duel, p2, row.player_2_team)

        return duel, duel_teams, p1, p2

    def _get_or_create_battle(self, session, row, duel, duel_teams, gvp, p1, p2):
        stage = self._get_or_create_stage(session, row.stage_name, gvp)

        battle = (
            session.query(Battle)
            .filter_by(
                duel_id=duel.id,
                order=int(row.battle_order),
            )
            .one_or_none()
        )

        if battle is None:
            battle = Battle(
                duel=duel,
                stage=stage,
                order=int(row.battle_order),
            )
            session.add(battle)

            c1 = self._get_or_create_character(
                session, row.character_1_name, gvp)
            c2 = self._get_or_create_character(
                session, row.character_2_name, gvp)

            session.add_all([
                BattleParticipant(
                    battle=battle,
                    player=p1,
                    game_character=c1,
                    duel_team=duel_teams.get("p1"),
                    position=1,
                ),
                BattleParticipant(
                    battle=battle,
                    player=p2,
                    game_character=c2,
                    duel_team=duel_teams.get("p2"),
                    position=2,
                ),
            ])

        return battle

    def _get_or_create_round(self, session, row, battle, p1, p2):
        round = (
            session.query(Round)
            .filter_by(
                battle_id=battle.id,
                order=int(row.round_order),
            )
            .one_or_none()
        )

        if round is None:
            round = Round(
                battle=battle,
                order=int(row.round_order),
            )
            session.add(round)

            session.add_all([
                RoundResult(
                    round=round,
                    player=p1,
                    result_code=row.player_1_result,
                ),
                RoundResult(
                    round=round,
                    player=p2,
                    result_code=row.player_2_result,
                ),
            ])

    # ──────────────────────────────────────────────
    # Helpers (idénticos al legacy)
    # ──────────────────────────────────────────────

    # _get_or_create_player
    # _get_or_create_country
    # _get_or_create_character
    # _get_or_create_stage
    # _get_or_create_game_version_platform
    # _get_or_create_simple
    # _parse_date

    def _get_or_create_player(self,
                              session: Session,
                              nickname: str,
                              country: Country
                              ):

        player = session.query(Player).filter_by(
            nickname=nickname).one_or_none()

        if player is None:
            player = Player(nickname=nickname, country=country)
            session.add(player)

        return player

    def _get_or_create_country(
        self,
        session: Session,
        iso_code: str,
        name: str,
    ) -> Country:

        if iso_code in self._country_cache:
            return self._country_cache[iso_code]

        country = (
            session.query(Country)
            .filter_by(iso_code=iso_code)
            .one_or_none()
        )

        if country is None:
            country = Country(
                iso_code=iso_code,
                name=name,
            )
            session.add(country)

        self._country_cache[iso_code] = country
        return country

    def _get_or_create_character(self,
                                 session: Session,
                                 name: str,
                                 game_version_platform: GameVersionPlatform
                                 ):

        identity = (
            session.query(CharacterIdentity)
            .filter_by(name=name, franchise=game_version_platform.game.name)
            .one_or_none()
        )

        if identity is None:
            identity = CharacterIdentity(
                name=name, franchise=game_version_platform.game.name)
            session.add(identity)

        # Asegura PKs
        session.flush()  # asegura identity.id y game_version_platform.id

        game_character = (
            session.query(GameCharacter)
            .filter_by(
                character_identity_id=identity.id,
                game_version_platform_id=game_version_platform.id,
            )
            .one_or_none()
        )

        if game_character is None:
            game_character = GameCharacter(
                character_identity=identity,
                game_version_platform=game_version_platform,
            )
            session.add(game_character)

        return game_character

    def _get_or_create_stage(self,
                             session: Session,
                             name: str,
                             game_version_platform: GameVersionPlatform
                             ):

        session.flush()

        stage = (
            session.query(Stage)
            .filter_by(
                name=name,
                game_version_platform_id=game_version_platform.id
            )
            .one_or_none()
        )

        if stage is None:
            stage = Stage(
                name=name,
                game_version_platform=game_version_platform
            )
            session.add(stage)

        return stage

    def _get_or_create_game_version_platform(self,
                                             session: Session,
                                             game: Game,
                                             platform: Platform,
                                             version: str
                                             ):
        '''
        Las versiones viven dentro de un juego, no son globales.
        '''
        session.flush()  # asegura game.id y platform.id

        gvp = (
            session.query(GameVersionPlatform)
            .filter_by(
                game_id=game.id,
                platform_id=platform.id,
                version=version
            )
            .one_or_none()
        )

        if gvp is None:
            gvp = GameVersionPlatform(
                game=game,
                platform=platform,
                version=version
            )
            session.add(gvp)
        return gvp

    def _get_or_create_simple(self,
                              session: Session,
                              model: Base,
                              name: str
                              ):
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

    def _attach_team(
        self,
        session: Session,
        duel: Duel,
        player: Player,
        team_name: str | None
    ) -> DuelTeam | None:

        if not team_name:
            return None

        team = self._get_or_create_team(session, team_name)

        duel_team = (
            session.query(DuelTeam)
            .filter_by(
                duel_id=duel.id,
                team_id=team.id
            )
            .one_or_none()
        )

        if duel_team is None:
            duel_team = DuelTeam(
                duel=duel,
                team=team
            )
            session.add(duel_team)

        member = (
            session.query(DuelTeamMember)
            .filter_by(
                duel_team_id=duel_team.id,
                player_id=player.id
            )
            .one_or_none()
        )

        if member is None:
            member = DuelTeamMember(
                duel_team=duel_team,
                player=player
            )
            session.add(member)

        return duel_team

    def _get_or_create_team(self, session: Session, name: str) -> Team:
        team = session.query(Team).filter_by(name=name).one_or_none()

        if team is None:
            team = Team(name=name)
            session.add(team)

        return team
