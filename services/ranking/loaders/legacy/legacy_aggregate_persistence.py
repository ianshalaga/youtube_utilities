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

from services.ranking.loaders.legacy.legacy_season_aggregator import (
    NormalizedSeasonAggregate,
    NormalizedEventAggregate
)

from services.ranking.storage.models import (
    Season, Event, Duel, Battle, Round,
    Region, Platform, EventType, Franchise,
    Game, GameVersionPlatform
)


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
                    duel_model = self._persist_duel(duel, event_model)

                    for battle in duel.battles:
                        battle_model = self._persist_battle(battle, duel_model)

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

    def _persist_season(self, season: NormalizedSeasonAggregate):
        return self._get_or_create(
            Season,
            name=season.season_name,
            defaults={
                "start_date": season.start_date,
                "end_date": season.end_date,
            }
        )

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

    def _persist_duel(self, duel, event_model):
        # create Duel ORM
        ...

    def _persist_battle(self, battle, duel_model):
        # create Battle ORM
        ...

    def _persist_rounds(self, battle, battle_model):
        # create Round ORM
        ...

    def _persist_participants(self, battle, duel_model):
        # create DuelParticipant ORM
        ...
