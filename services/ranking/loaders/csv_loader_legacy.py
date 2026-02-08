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
from sqlalchemy.orm import Session

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


class CSVLoaderLegacy(DataLoader):
    def __init__(self, csv_path: Path):
        if not csv_path.exists():
            raise FileNotFoundError(csv_path)
        self._csv_path = csv_path
        self._country_cache: dict[str, Country] = {}

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

    def _load_csv(self, session: Session):
        '''
        CSV perfectamente ordenado.
        No existen rounds parciales (un solo "0").
        '''
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

            for raw_row in reader:
                row = RowLegacyMapper(raw_row)

                # @@@@ SEASON

                season_key = (row.season_name)

                if season_key != last_season_key:
                    current_season = self._get_or_create_season(session, row)
                    last_season_key = season_key
                    event_order = 0

                # @@@@ EVENT

                event_key = (
                    row.season_name.strip(),
                    row.event_name.strip(),
                )

                if event_key != last_event_key:
                    event_order += 1
                    current_event, game_version_platform, franchise = self._get_or_create_event(
                        session, row, current_season, event_order)
                    last_event_key = event_key
                    current_duel = None
                    last_duel_key = None

                # @@@@ DUEL

                duel_key = (
                    last_event_key,      # identidad REAL del evento
                    row.duel_order,      # ordinal local al evento
                )

                if duel_key != last_duel_key:
                    current_duel, duel_teams, player_1, player_2 = self._get_or_create_duel(
                        session, current_event, row)
                    last_duel_key = duel_key
                    current_battle = None
                    last_battle_key = None
                    battle_order = 0

                # @@@@ BATTLE

                battle_key = (
                    last_event_key,
                    row.duel_order,
                    row.combat_order,
                )

                if battle_key != last_battle_key:
                    battle_order += 1
                    current_battle = self._get_or_create_battle(
                        session,
                        current_duel,
                        row,
                        battle_order,
                        duel_teams,
                        game_version_platform,
                        player_1,
                        player_2,
                        franchise
                    )
                    last_battle_key = battle_key

                # @@@@ ROUNDS
                self._create_rounds(
                    session,
                    current_battle,
                    row,
                    player_1,
                    player_2
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

    def _get_or_create_event(self,
                             session: Session,
                             row: RowLegacyMapper,
                             season: Season,
                             event_order: int
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
            order=event_order,
            event_type=event_type,
            region=region,
            game_version_platform=game_version_platform,
            bracket_url=row.event_brackets,
            playlist_url=row.event_playlist,
        )

        session.add(event)
        return (event, game_version_platform, franchise)

    def _get_or_create_duel(self,
                            session: Session,
                            event: Event,
                            row: RowLegacyMapper
                            ):

        duel_type = self._get_or_create_simple(
            session, DuelType, row.duel_type
        )

        duel = Duel(
            event=event,
            duel_type=duel_type,
            order=int(row.duel_order),
            video_url=row.duel_video,
        )

        session.add(duel)

        # Countries
        p1_country = self._get_or_create_country(
            session, country_name_to_iso(row.player_1_country), row.player_1_country)
        p2_country = self._get_or_create_country(
            session, country_name_to_iso(row.player_2_country), row.player_2_country)

        # Participants
        p1 = self._get_or_create_player(session, row.player_1_name, p1_country)
        p2 = self._get_or_create_player(session, row.player_2_name, p2_country)

        session.add(DuelParticipant(duel=duel, player=p1))
        session.add(DuelParticipant(duel=duel, player=p2))

        duel_teams = {}

        if row.player_1_team:
            team = self._get_or_create_simple(
                session, Team, row.player_1_team)

            session.flush()

            duel_team = (
                session.query(DuelTeam)
                .filter_by(
                    duel_id=duel.id,
                    team_id=team.id,
                )
                .one_or_none()
            )

            if duel_team is None:
                duel_team = DuelTeam(duel=duel, team=team)
                session.add(duel_team)

            duel_teams["p1"] = duel_team

            session.add(DuelTeamMember(duel_team=duel_team, player=p1))

        if row.player_2_team:
            team = self._get_or_create_simple(
                session, Team, row.player_2_team)

            session.flush()

            duel_team = (
                session.query(DuelTeam)
                .filter_by(
                    duel_id=duel.id,
                    team_id=team.id,
                )
                .one_or_none()
            )

            if duel_team is None:
                duel_team = DuelTeam(duel=duel, team=team)
                session.add(duel_team)

            duel_teams["p2"] = duel_team

            session.add(DuelTeamMember(duel_team=duel_team, player=p2))

        return (duel, duel_teams, p1, p2)

    def _get_or_create_battle(self,
                              session: Session,
                              duel: Duel,
                              row: RowLegacyMapper,
                              battle_order: int,
                              duel_teams: dict[str, DuelTeam],
                              game_version_platform: GameVersionPlatform,
                              p1: Player,
                              p2: Player,
                              franchise: Franchise
                              ):

        stage = self._get_or_create_stage(
            session, row.stage_name, game_version_platform)

        battle = Battle(
            duel=duel,
            stage=stage,
            order=battle_order,
        )

        session.add(battle)

        c1 = self._get_or_create_character(
            session, row.character_1_name, franchise, game_version_platform)
        c2 = self._get_or_create_character(
            session, row.character_2_name, franchise, game_version_platform)

        duel_team_p1 = duel_teams.get("p1")
        duel_team_p2 = duel_teams.get("p2")

        session.add(BattleParticipant(
            battle=battle,
            player=p1,
            game_character=c1,
            duel_team=duel_team_p1,
            position=1
        ))

        session.add(BattleParticipant(
            battle=battle,
            player=p2,
            game_character=c2,
            duel_team=duel_team_p2,
            position=2
        ))

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
