"""
Legacy Aggregate Persistence
============================

Responsabilidad:

- Traducir NormalizedSeasonAggregate a entidades ORM.
- Persistir árbol completo:
    Season → Event → Duel → Battle → Round → Participants
- Operar dentro de una sesión SQLAlchemy.

No:
- Ejecuta agregación.
- Valida dominio.
- Lee CSV.
- Deriva lógica.

Es una capa de infraestructura.
"""

from typing import Tuple
from sqlalchemy.orm import Session

from services.ranking.loaders.legacy.legacy_season_aggregator import NormalizedSeasonAggregate
from services.ranking.loaders.legacy.legacy_event_aggregator import NormalizedEventAggregate
from services.ranking.loaders.legacy.legacy_duel_aggregator import NormalizedDuelAggregate
from services.ranking.loaders.legacy.row_legacy_normalizer import NormalizedParticipant


from services.ranking.storage.models import (
    Season, Event, Duel, Battle, Round,
    Region, Platform, EventType, Franchise,
    Game, GameVersionPlatform, DuelType,
    Country, Player, Team, Stage
)

_COUNTRY_NAME_ISO_CODE_3166_ALPHA_2_MAP = {
    "Argentina": "AR",
    "Chile": "CL",
    "Paraaguay": "PY",
    "Brasil": "BR",
}


class LegacyAggregatePersistence:
    """
    Servicio de persistencia de aggregates legacy.

    Traductor entre modelo normalizado y modelo ORM.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # ---------------------------------------------------------

    def persist(
        self,
        seasons: Tuple[NormalizedSeasonAggregate, ...]
    ) -> None:
        """
        Persiste el árbol completo de aggregates.

        Se asume que los aggregates son coherentes.
        """

        for season in seasons:
            season_model = self._persist_season(season)

            for event in season.events:
                region_model = self._persist_region(event)
                event_type_model = self._persist_event_type(event)
                platform_model = self._persist_platform(event)
                game_franchise_model = self._persist_game_franchise(event)
                game_model = self._persist_game(event, game_franchise_model)
                game_version_platform_model = self._persist_game_version_platform(
                    event, game_model, platform_model)

                event_model = self._persist_event(
                    event,
                    season_model,
                    region_model,
                    event_type_model,
                    game_version_platform_model
                )

                for duel in event.duels:
                    duel_type_model = self._persist_duel_type(duel)
                    team_duel_type_model = self._persist_team_duel_type(duel)
                    players: set[Player] = set()
                    teams: set[Team] = set()
                    for battle in duel.battles:
                        for participant in battle.participants:
                            country_model = self._persist_country(participant)
                            player_model = self._persist_player(
                                participant, country_model)
                            team_model = self._persist_team(participant)

                            players.add(player_model)
                            teams.add(team_model)

                    winner_player_model = None
                    for player in players:
                        if player.nickname == duel.winner_player_name:
                            winner_player_model = player
                            break

                    winner_team_model = None  # TODO
                    # for team in teams:
                    #     if team.name == duel.winner_team_name:
                    #         winner_team_model = team
                    #         break

                    duel_model = self._persist_duel(
                        duel,
                        event_model,
                        duel_type_model,
                        team_duel_type_model,
                        winner_player_model,
                        winner_team_model
                    )

                    for battle in duel.battles:
                        stage_model = self._persist_stage(
                            battle, game_version_platform_model)
                        winner_model = None  # TODO
                        loser_model = None  # TODO

                        battle_model = self._persist_battle(
                            battle,
                            duel_model,
                            stage_model,
                            winner_model,
                            loser_model
                        )

                        self._persist_rounds(battle, battle_model)
                        self._persist_participants(battle, duel_model)

        self._session.flush()

    # ---------------------------------------------------------
    # Private persistence helpers
    # ---------------------------------------------------------

    def _get_or_create(self, model: type, defaults=dict[str: any] | None, **kwargs) -> object:
        """
        Patrón genérico get_or_create.

        - Busca por kwargs.
        - Si no existe, crea con kwargs + defaults.
        """

        instance = (
            self._session.query(model)
            .filter_by(**kwargs)
            .one_or_none()
        )

        if instance:
            return instance

        params = dict(kwargs)
        if defaults:
            params.update(defaults)

        instance = model(**params)
        self._session.add(instance)
        self._session.flush()  # asegura PK disponible

        return instance

    # SEASON persistence
    def _persist_season(self, season: NormalizedSeasonAggregate):
        return self._get_or_create(
            Season,
            name=season.season_name,
            defaults={
                "start_date": season.start_date,
                "end_date": season.end_date,
            }
        )

    # EVENT persistence
    def _persist_region(self, event: NormalizedEventAggregate):
        return self._get_or_create(
            Region,
            name=event.region_name
        )

    def _persist_event_type(self, event: NormalizedEventAggregate):
        return self._get_or_create(
            EventType,
            name=event.event_type_name
        )

    def _persist_platform(self, event: NormalizedEventAggregate):
        return self._get_or_create(
            Platform,
            name=event.platform_name
        )

    def _persist_game_franchise(self, event: NormalizedEventAggregate):
        return self._get_or_create(
            Franchise,
            name=event.game_franchise_name
        )

    def _persist_game(self, event: NormalizedEventAggregate, game_franchise_model: Franchise):
        return self._get_or_create(
            Game,
            name=event.game_name,
            franchise_id=game_franchise_model.id
        )

    def _persist_game_version_platform(
        self,
        event: NormalizedEventAggregate,
        game_model: Game,
        platform_model: Platform
    ):
        return self._get_or_create(
            GameVersionPlatform,
            game_id=game_model.id,
            platform_id=platform_model.id,
            version=event.game_version
        )

    def _persist_event(
        self,
        event: NormalizedEventAggregate,
        season_model: Season,
        region_model: Region,
        event_type_model: EventType,
        game_version_platform_model: GameVersionPlatform
    ):
        return self._get_or_create(
            Event,
            name=event.event.event_name,
            season_id=season_model.id,
            region_id=region_model.id,
            event_type_id=event_type_model.id,
            game_version_platform_id=game_version_platform_model.id,
            defaults={
                "event_date": event.event.event_date,
                "sequence_number": event.event_sequence_number,
                "bracket_url": event.event.brackets_url,
                "playlist_url": event.event.playlist_url
            }
        )

    # DUEL persistence
    def _persist_duel_type(self, duel: NormalizedDuelAggregate):
        return self._get_or_create(
            DuelType,
            name=duel.duel.normal_duel_type_name
        )

    def _persist_team_duel_type(self, duel: NormalizedDuelAggregate):
        return self._get_or_create(
            DuelType,
            name=duel.duel.team_duel_type_name
        )

    def _persist_country(self, participant: NormalizedParticipant):
        return self._get_or_create(
            Country,
            name=participant.country,
            iso_code=_COUNTRY_NAME_ISO_CODE_3166_ALPHA_2_MAP[participant.country]
        )

    def _persist_player(self, participant: NormalizedParticipant, country_model: Country):
        return self._get_or_create(
            Player,
            nickname=participant.player_name,
            country_id=country_model.id
        )

    def _persist_team(self, participant: NormalizedParticipant):
        return self._get_or_create(
            Team,
            name=participant.team_name
        )

    def _persist_duel(
        self,
        duel: NormalizedDuelAggregate,
        event_model: Event,
        duel_type_model: DuelType,
        team_duel_type_model: DuelType,
        winner_player_model: Player,
        winner_team_model: Team
    ):
        return self._get_or_create(
            Duel,
            event_id=event_model.id,
            duel_type_id=duel_type_model.id,
            team_duel_type_id=team_duel_type_model.id,
            winner_id=winner_player_model.id,
            winner_team_id=winner_team_model.id,
            defaults={
                "is_team_duel": duel.duel.is_team_duel,
                "sequence_number": duel.duel.normal_duel_sequence_number,
                "team_duel_sequence_number": duel.duel.team_duel_sequence_number,
                "video_url": duel.duel.duel_video_url
            }
        )

    # BATTLE persistence
    def _persist_stage(self, battle, game_version_platform_model):
        return (
            self._get_or_create(
                Stage,
                name=battle.stage_name,
                game_version_platform_id=game_version_platform_model.id
            )
        )

    def _persist_battle(self, battle, duel_model):
        # create Battle ORM
        ...

    def _persist_rounds(self, battle, battle_model):
        # create Round ORM
        ...

    def _persist_participants(self, battle, duel_model):
        # create DuelParticipant ORM
        ...
