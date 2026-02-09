from collections import defaultdict

from domain.ranking.entities.ranking_entity import RankingEntity
from domain.ranking.models.battle_event import BattleEvent
from domain.ranking.models.duel_event import DuelEvent
from services.ranking.filters import RankingQuery
from services.ranking.storage.repository import RankingRepository
from services.ranking.loaders.mappers.event_type_mapper import EventType as EventTypeEnum


class RankingDBProvider:
    """
    Provider DB → Domain.

    RESPONSABILIDADES:
    - Obtener datos desde repository
    - Construir BattleEvent (battle-level)
    - Agrupar BattleEvent → DuelEvent (duel-level)
    - Resolver nivel competitivo (PLAYER / TEAM)
    """

    def __init__(self, *, session, repository: RankingRepository):
        self._session = session
        self._repository = repository

        self._battle_cache: dict[str, list[BattleEvent]] = {}
        self._duel_cache: dict[str, list[DuelEvent]] = {}

    # ──────────────────────────────────────────────────────────
    # API pública
    # ──────────────────────────────────────────────────────────

    def _cache_key(self, query: RankingQuery, scope: str) -> str:
        return f"{scope}:{repr(query)}"

    def iter_battles(self, query: RankingQuery) -> list[BattleEvent]:
        key = self._cache_key(query, "battles")

        if key not in self._battle_cache:
            self._battle_cache[key] = self._build_battle_events(query)

        return self._battle_cache[key]

    def iter_duels(self, query: RankingQuery) -> list[DuelEvent]:
        key = self._cache_key(query, "duels")

        if key not in self._duel_cache:
            battles = self.iter_battles(query)
            self._duel_cache[key] = self._build_duel_events_from_battles(
                battles)

        return self._duel_cache[key]

    # ──────────────────────────────────────────────────────────
    # Construcción battle-level
    # ──────────────────────────────────────────────────────────

    def _build_battle_events(self, query: RankingQuery) -> list[BattleEvent]:
        """
        RoundResult → BattleEvent
        """

        round_results = self._repository.fetch_round_results(
            session=self._session,
            ranking_query=query,
        )

        grouped: dict[int, list] = defaultdict(list)
        for rr in round_results:
            grouped[rr.round.battle.id].append(rr)

        battle_events: list[BattleEvent] = []

        for battle_id, rounds in grouped.items():
            duel_id = rounds[0].round.battle.duel_id

            battle_events.append(
                BattleEvent.from_round_results(
                    battle_id=battle_id,
                    duel_id=duel_id,
                    round_results=rounds,
                )
            )

        return battle_events

    # ──────────────────────────────────────────────────────────
    # Construcción duel-level
    # ──────────────────────────────────────────────────────────

    def _build_duel_events_from_battles(
        self,
        battles: list[BattleEvent],
    ) -> list[DuelEvent]:
        """
        BattleEvent → DuelEvent
        """

        grouped: dict[int, list[BattleEvent]] = defaultdict(list)
        for battle in battles:
            grouped[battle.duel_id].append(battle)

        duel_events: list[DuelEvent] = []

        for duel_id, duel_battles in grouped.items():
            duel_events.append(
                self._build_single_duel_event(
                    duel_id=duel_id,
                    battles=duel_battles,
                )
            )

        return duel_events

    def _build_single_duel_event(
        self,
        *,
        duel_id: int,
        battles: list[BattleEvent],
    ) -> DuelEvent:
        """
        Construye UN DuelEvent coherente.
        """

        # Determinar tipo de evento
        event_type = self._repository.fetch_duel_event_type(
            session=self._session,
            duel_id=duel_id,
        )

        if event_type.name == EventTypeEnum.TEAM_TOURNAMENT.value:
            competitive_level = RankingEntity.TEAM
        else:
            competitive_level = RankingEntity.PLAYER

        # Resolver afiliaciones (solo TEAM)
        if competitive_level is RankingEntity.TEAM:
            player_affiliations = self._repository.fetch_duel_player_affiliations(
                session=self._session,
                duel_id=duel_id,
            )
        else:
            player_affiliations = {}

        # Construir DuelEvent
        return DuelEvent.from_battle_events(
            battles=battles,
            competitive_level=competitive_level,
            player_affiliations=player_affiliations,
        )
