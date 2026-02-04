from collections import defaultdict
from typing import Iterable

from sqlalchemy.orm import Session

from services.ranking.filters import RankingQuery
from services.ranking.providers.base import DataProvider
from services.ranking.storage.repository import RankingRepository
from services.ranking.storage.session import SessionLocal

from domain.ranking.models.battle_event import BattleEvent
from domain.ranking.models.duel_event import DuelEvent


class RankingDBProvider(DataProvider):
    """
    Proveedor de datos de ranking desde base SQL.
    """

    def __init__(
        self,
        repository: RankingRepository | None = None,
    ) -> None:
        self._repository = repository or RankingRepository()

        # Cache interno por instancia
        self._battle_cache: dict[int, list[BattleEvent]] = {}
        self._duel_cache: dict[int, list[DuelEvent]] = {}

    # ─────────────────────────────────────────────────────────
    # API pública
    # ─────────────────────────────────────────────────────────

    def iter_battles(
        self,
        query: RankingQuery,
    ) -> Iterable[BattleEvent]:
        query_key = id(query)

        if query_key not in self._battle_cache:
            with SessionLocal() as session:
                self._battle_cache[query_key] = self._build_battle_events(
                    session, query
                )

        return self._battle_cache[query_key]

    def iter_duels(
        self,
        query: RankingQuery,
    ) -> Iterable[DuelEvent]:
        query_key = id(query)

        if query_key not in self._duel_cache:
            # Reutilizamos battles si ya existen
            battles = self.iter_battles(query)

            self._duel_cache[query_key] = self._build_duel_events_from_battles(
                battles
            )

        return self._duel_cache[query_key]

    # ─────────────────────────────────────────────────────────
    # Construcción interna
    # ─────────────────────────────────────────────────────────

    def _build_battle_events(
        self,
        session: Session,
        query: RankingQuery,
    ) -> list[BattleEvent]:
        round_results = self._repository.fetch_round_results(
            session=session,
            ranking_query=query,
        )

        battles: dict[int, list] = defaultdict(list)

        for rr in round_results:
            battles[rr.round.battle.id].append(rr)

        return [
            BattleEvent.from_round_results(battle_rounds)
            for battle_rounds in battles.values()
        ]

    def _build_duel_events_from_battles(
        self,
        battle_events: list[BattleEvent],
    ) -> list[DuelEvent]:
        duels: dict[int, list[BattleEvent]] = defaultdict(list)

        for battle in battle_events:
            duels[battle.duel_id].append(battle)

        duel_events: list[DuelEvent] = []

        for battles in duels.values():
            competitive_level, player_affiliations = (
                self._resolve_duel_competitive_context(battles)
            )

            duel_events.append(
                DuelEvent.from_battle_events(
                    battles,
                    competitive_level=competitive_level,
                    player_affiliations=player_affiliations,
                )
            )

        return duel_events
