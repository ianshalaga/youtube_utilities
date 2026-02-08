"""
CSV Loader Legacy

La carga es transaccional y debe ejecutarse dentro de
una sesión controlada por la capa de aplicación.

Este loader:
- NO persiste datos calculados
- Respeta orden temporal
- Crea entidades si no existen
- Realiza rollback completo ante cualquier error
"""

import csv
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from dataclasses import dataclass

from services.ranking.storage.session import SessionLocal
from services.ranking.loaders.base import DataLoader
from services.ranking.storage.base import Base
from services.ranking.loaders.mappers.row_legacy_mapper import RowLegacyMapper
from services.ranking.loaders.mappers.event_type_mapper import resolve_event_type
from services.ranking.loaders.mappers.country_mapper import country_name_to_iso

from services.ranking.storage.models import (
    Season, Event, Duel, Battle, Round,
    Player, Country, Team,
    DuelParticipant, DuelTeam, DuelTeamMember,
    BattleParticipant, RoundResult,
    Game, Platform, GameVersionPlatform,
    GameCharacter, CharacterIdentity,
    EventType, Region, DuelType, Stage,
    Franchise
)


@dataclass
class _LoaderState:
    season = None
    event = None
    duel = None
    battle = None

    last_event_key: str | None = None
    last_duel_order: int | None = None
    last_combat_order: int | None = None

    duel_has_teams: bool = False


class CSVLoaderLegacy(DataLoader):
    def __init__(self, csv_path: Path):
        if not csv_path.exists():
            raise FileNotFoundError(csv_path)
        self._csv_path = csv_path
        self._country_cache: dict[str, Country] = {}

    # ──────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────

    def load(self, session, csv_path):
        state = _LoaderState()

        for row in self._iter_rows(csv_path):
            self._process_row(session, row, state)

        session.commit()

    # ──────────────────────────────────────────────
    # Core loader
    # ──────────────────────────────────────────────

    def _process_row(self, session: Session, row: RowLegacyMapper, state: _LoaderState) -> None:
        # ──────────────────────────────────────
        # SEASON
        # ──────────────────────────────────────
        if state.season is None or row.season_name != state.season.name:
            state.season = self._get_or_create_season(session, row)
            state.event = None
            state.duel = None
            state.battle = None
            state.last_event_key = None
            state.last_duel_order = None
            state.last_combat_order = None

        # ──────────────────────────────────────
        # EVENT (clave REAL, no solo nombre)
        # ──────────────────────────────────────
        event_key = (
            state.season.id,
            row.event_name.strip(),
        )

        if event_key != state.last_event_key:
            state.event = self._get_or_create_event(session, state.season, row)
            state.last_event_key = event_key
            state.duel = None
            state.battle = None
            state.last_duel_order = None
            state.last_combat_order = None

        # ──────────────────────────────────────
        # DUEL (ORDINAL LOCAL AL EVENTO)
        # ──────────────────────────────────────
        if row.duel_order != state.last_duel_order:
            state.duel = self._create_duel(session, state.event, row)
            state.last_duel_order = row.duel_order
            state.battle = None
            state.last_combat_order = None
            state.duel_has_teams = False

        # ──────────────────────────────────────
        # DETECCIÓN DE TEAMS (INCREMENTAL)
        # ──────────────────────────────────────
        if row.player_1_team or row.player_2_team:
            self._assign_teams_to_duel(session, state.duel, row)

        # ──────────────────────────────────────
        # BATTLE (ORDINAL LOCAL AL DUEL)
        # ──────────────────────────────────────
        if row.combat_order != state.last_combat_order:
            state.battle = self._create_battle(session, state.duel, row)
            state.last_combat_order = row.combat_order

        # ──────────────────────────────────────
        # ROUND + PARTICIPANTS
        # ──────────────────────────────────────
        self._create_round_and_participants(
            session=session,
            battle=state.battle,
            row=row,
        )

    # Entity creation helpers

    # @@@@ Externos (Season > Event > Duel > Battle > Round)

    def _get_or_create_season(self,
                              session: Session,
                              row: RowLegacyMapper
                              ):
        '''
        La fecha de inicio de la temporada se deduce
        de la fecha del primer evento de la misma.
        '''
        season = session.query(Season).filter_by(
            name=row.season_name).one_or_none()

        if season is None:
            season = Season(
                name=row.season_name,
                start_date=self._parse_date(row.event_date)
            )

            session.add(season)

        return season

    def _get_or_create_event(
        self,
        session: Session,
        season: Season,
        row: RowLegacyMapper,
    ):

        event_type_name = resolve_event_type(row.event_name)

        event_type = self._get_or_create_simple(
            session, EventType, event_type_name)

        region = self._get_or_create_simple(
            session, Region, row.region_name)

        franchise = self._get_or_create_simple(
            session, Franchise, "Soulcalibur")

        game = (
            session.query(Game)
            .filter_by(name=row.game_name)
            .one_or_none()
        )

        if game is None:
            game = Game(
                name=row.game_name,
                franchise=franchise
            )
            session.add(game)

        platform = self._get_or_create_simple(
            session, Platform, row.event_platform)

        game_version_platform = self._get_or_create_game_version_platform(
            session, game, platform, row.game_version)

        event = Event(
            name=row.event_name,
            event_date=self._parse_date(row.event_date),
            season=season,
            order=row.event_order,
            event_type=event_type,
            region=region,
            game_version_platform=game_version_platform,
            bracket_url=row.event_brackets,
            playlist_url=row.event_playlist,
        )

        session.add(event)
        return (event, game_version_platform, franchise)

    def _create_duel(self, session: Session, event: Event, row: RowLegacyMapper):
        duel = Duel(
            event=event,
            order=row.duel_order,
        )
        session.add(duel)
        session.flush()
        return duel

    def _assign_teams_to_duel(self, session: Session, duel: Duel, row: RowLegacyMapper):
        if row.player_1_team:
            team = self._get_or_create_team(session, row.player_1_team)
            self._add_player_to_team(session, duel, row.player_1_name, team)

        if row.player_2_team:
            team = self._get_or_create_team(session, row.player_2_team)
            self._add_player_to_team(session, duel, row.player_2_name, team)

    def _create_battle(self, session: Session, duel: Duel, row: RowLegacyMapper):
        stage = self._get_or_create_stage(...)
        battle = Battle(duel=duel, order=row.combat_order, stage=stage)
        session.add(battle)
        session.flush()
        return battle

    def _create_rounds(self,
                       session: Session,
                       battle: Battle,
                       row: RowLegacyMapper,
                       p1: Player,
                       p2: Player
                       ):
        """
        Crea rounds y resultados a partir del mapper legacy.
        """
        # p1 = session.query(Player).filter_by(nickname=row.player_1_name).one()
        # p2 = session.query(Player).filter_by(nickname=row.player_2_name).one()

        for i in range(1, 6):
            r1 = row.round_result(i, player=1)
            r2 = row.round_result(i, player=2)

            # No hubo round
            if r1 == "0" or r2 == "0":
                continue

            round = Round(
                battle=battle,
                order=i,
            )

            session.add(round)

            session.add_all([
                RoundResult(
                    round=round,
                    player=p1,
                    result_code=r1,
                ),
                RoundResult(
                    round=round,
                    player=p2,
                    result_code=r2,
                ),
            ])

    # @@@@ Internos

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

    def _get_or_create_character(self,
                                 session: Session,
                                 name: str,
                                 franchise: Franchise,
                                 game_version_platform: GameVersionPlatform
                                 ):

        identity = (
            session.query(CharacterIdentity)
            .filter_by(
                name=name,
                franchise_id=franchise.id
            )
            .one_or_none()
        )

        if identity is None:
            identity = CharacterIdentity(
                name=name,
                franchise=franchise
            )
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

    # @@@@ Utilidades

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
