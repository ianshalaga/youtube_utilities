from collections import defaultdict
from typing import Iterable

from sqlalchemy.orm import Session

from services.ranking.filters import RankingQuery
from services.ranking.providers.base import DataProvider
from services.ranking.storage.repository import RankingRepository
from services.ranking.loaders.mappers.event_type_mapper import EventType

from domain.ranking.entities.ranking_entity import RankingEntity
from domain.ranking.models.battle_event import BattleEvent
from domain.ranking.models.duel_event import DuelEvent


class RankingDBProvider(DataProvider):

    def __init__(
        self,
        *,
        session: Session,
        repository: RankingRepository | None = None,
    ) -> None:
        self._session = session
        self._repository = repository or RankingRepository()

        self._battle_cache: dict[int, list[BattleEvent]] = {}
        self._duel_cache: dict[int, list[DuelEvent]] = {}

    def iter_battles(self, query: RankingQuery) -> Iterable[BattleEvent]:
        key = id(query)
        if key not in self._battle_cache:
            self._battle_cache[key] = self._build_battle_events(query)
        return self._battle_cache[key]

    def iter_duels(self, query: RankingQuery) -> Iterable[DuelEvent]:
        key = id(query)
        if key not in self._duel_cache:
            battles = self.iter_battles(query)
            self._duel_cache[key] = self._build_duel_events_from_battles(
                battles)
        return self._duel_cache[key]

    def _build_battle_events(self, query: RankingQuery) -> list[BattleEvent]:
        round_results = self._repository.fetch_round_results(
            session=self._session,
            ranking_query=query,
        )

        grouped: dict[int, list] = defaultdict(list)
        for rr in round_results:
            grouped[rr.round.battle.id].append(rr)

        return [
            BattleEvent.from_round_results(r)
            for r in grouped.values()
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

            if competitive_level is RankingEntity.TEAM:
                valid_players = {
                    pid for pid, tid in player_affiliations.items()
                    if tid is not None
                }

                battles = [
                    b.with_filtered_participants(valid_players)
                    for b in battles
                ]

            duel_events.append(
                DuelEvent.from_battle_events(
                    battles,
                    competitive_level=competitive_level,
                    player_affiliations=player_affiliations,
                )
            )

        return duel_events

    def _resolve_duel_competitive_context(
        self,
        battles: list[BattleEvent],
    ) -> tuple[RankingEntity, dict[int, int | None]]:

        duel_id = battles[0].duel_id

        player_affiliations = self._repository.fetch_duel_player_affiliations(
            session=self._session,
            duel_id=duel_id,
        )

        # 🔑 FUENTE DE VERDAD
        event_type = battles[0].event_type

        if event_type == EventType.TEAM_TOURNAMENT:
            competitive_level = RankingEntity.TEAM
        else:
            competitive_level = RankingEntity.PLAYER

        return competitive_level, player_affiliations
