"""
RankingDBProvider

Proveedor de datos de ranking basado en base de datos.
Convierte datos persistidos (ORM) en eventos de dominio.
"""

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

    Produce:
    - BattleEvent  → ranking por Character / Player+Character
    - DuelEvent    → ranking por Player / Team
    """

    def __init__(
        self,
        repository: RankingRepository | None = None,
    ) -> None:
        self._repository = repository or RankingRepository()

    # ─────────────────────────────────────────────────────────
    # API pública
    # ─────────────────────────────────────────────────────────

    def iter_battles(
        self,
        query: RankingQuery,
    ) -> Iterable[BattleEvent]:
        """
        Devuelve BattleEvent para cálculos de ranking
        basados en battles.
        """
        with SessionLocal() as session:
            return self._build_battle_events(session, query)

    def iter_duels(
        self,
        query: RankingQuery,
    ) -> Iterable[DuelEvent]:
        """
        Devuelve DuelEvent para cálculos de ranking
        basados en duelos.
        """
        with SessionLocal() as session:
            return self._build_duel_events(session, query)

    # ─────────────────────────────────────────────────────────
    # Implementación interna
    # ─────────────────────────────────────────────────────────

    def _build_battle_events(
        self,
        session: Session,
        query: RankingQuery,
    ) -> list[BattleEvent]:
        """
        Construye BattleEvent agrupando RoundResult por battle.
        """

        round_results = self._repository.fetch_round_results(
            session=session,
            ranking_query=query,
        )

        battles: dict[int, list] = defaultdict(list)

        for rr in round_results:
            battle_id = rr.round.battle.id
            battles[battle_id].append(rr)

        battle_events: list[BattleEvent] = []

        for battle_rounds in battles.values():
            battle_events.append(
                BattleEvent.from_round_results(battle_rounds)
            )

        return battle_events

    def _build_duel_events(
        self,
        session: Session,
        query: RankingQuery,
    ) -> list[DuelEvent]:
        """
        Construye DuelEvent agrupando BattleEvent por duelo.
        """

        battle_events = self._build_battle_events(session, query)

        duels: dict[int, list[BattleEvent]] = defaultdict(list)

        for battle_event in battle_events:
            duels[battle_event.duel_id].append(battle_event)

        duel_events: list[DuelEvent] = []

        for battle_list in duels.values():
            duel_events.append(
                DuelEvent.from_battle_events(battle_list)
            )

        return duel_events
