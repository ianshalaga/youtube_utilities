from collections import defaultdict

from domain.ranking.entities.ranking_entity import RankingEntity
from domain.ranking.models.battle_event import BattleEvent
from domain.ranking.models.duel_event import DuelEvent
from services.ranking.storage.repository import RankingRepository
from services.ranking.filters import RankingQuery


class RankingDBProvider:
    def __init__(self, *, session, repository: RankingRepository):
        self._session = session
        self._repository = repository

        self._battle_cache: dict[str, list[BattleEvent]] = {}
        self._duel_cache: dict[str, list[DuelEvent]] = {}

    # ──────────────────────────────────────────────
    # Cache helpers
    # ──────────────────────────────────────────────

    def _cache_key(self, query: RankingQuery, scope: str) -> str:
        return f"{scope}:{repr(query)}"

    # ──────────────────────────────────────────────
    # Battles
    # ──────────────────────────────────────────────

    def iter_battles(self, query: RankingQuery) -> list[BattleEvent]:
        key = self._cache_key(query, "battles")

        if key not in self._battle_cache:
            self._battle_cache[key] = self._build_battle_events(query)

        return self._battle_cache[key]

    def _build_battle_events(self, query: RankingQuery) -> list[BattleEvent]:
        round_results = self._repository.fetch_round_results(
            session=self._session,
            ranking_query=query,
        )

        by_battle: dict[int, list] = defaultdict(list)
        duel_ids: dict[int, int] = {}

        for r in round_results:
            battle = r.round.battle
            battle_id = battle.id
            duel_id = battle.duel_id

            by_battle[battle_id].append(r)
            duel_ids[battle_id] = duel_id

        battles: list[BattleEvent] = []

        for battle_id, rounds in by_battle.items():
            battles.append(
                BattleEvent.from_round_results(
                    battle_id=battle_id,
                    duel_id=duel_ids[battle_id],
                    round_results=rounds,
                )
            )

        return battles

    # ──────────────────────────────────────────────
    # Duels
    # ──────────────────────────────────────────────

    def iter_duels(
        self,
        *,
        query: RankingQuery,
        competitive_level: RankingEntity,
    ) -> list[DuelEvent]:
        key = self._cache_key(query, "duels")

        if key not in self._duel_cache:
            battles = self.iter_battles(query)
            self._duel_cache[key] = self._build_duel_events_from_battles(
                battles=battles,
                competitive_level=competitive_level,
            )

        return self._duel_cache[key]

    def _build_duel_events_from_battles(
        self,
        *,
        battles: list[BattleEvent],
        competitive_level: RankingEntity,
    ) -> list[DuelEvent]:

        by_duel: dict[int, list[BattleEvent]] = defaultdict(list)

        for b in battles:
            by_duel[b.duel_id].append(b)

        duels: list[DuelEvent] = []

        for duel_id, duel_battles in by_duel.items():
            duels.append(
                self._build_single_duel_event(
                    duel_id=duel_id,
                    battles=duel_battles,
                    competitive_level=competitive_level,
                )
            )

        return duels

    def _build_single_duel_event(
        self,
        *,
        duel_id: int,
        battles: list[BattleEvent],
        competitive_level: RankingEntity,
    ) -> DuelEvent:

        participants: set[int] = set()
        for b in battles:
            participants.update(b.participants)

        winner_id, loser_ids = self._resolve_duel_result_from_battles(
            battles=battles,
        )

        return DuelEvent(
            duel_id=duel_id,
            competitive_level=competitive_level,
            participant_ids=tuple(sorted(participants)),
            winner_id=winner_id,
            loser_ids=tuple(loser_ids),
            battles=tuple(battles),
        )

    def _resolve_duel_result_from_battles(
        self,
        *,
        battles: list[BattleEvent],
    ) -> tuple[int, tuple[int, ...]]:
        """
        Determina ganador y perdedores del duelo a partir de las battles.
        """

        wins_by_participant: dict[int, int] = {}

        for battle in battles:
            # Determinar ganador de la battle por raw_points
            raw_points = battle.raw_points_by_participant

            if not raw_points:
                raise ValueError(
                    f"Battle {battle.battle_id} sin raw_points"
                )

            max_points = max(raw_points.values())
            winners = [
                pid for pid, pts in raw_points.items()
                if pts == max_points
            ]

            if len(winners) != 1:
                raise ValueError(
                    f"Battle {battle.battle_id} empatada o ambigua"
                )

            winner_id = winners[0]
            wins_by_participant[winner_id] = (
                wins_by_participant.get(winner_id, 0) + 1
            )

        if not wins_by_participant:
            raise ValueError("No se puede resolver duelo sin battles")

        max_wins = max(wins_by_participant.values())
        duel_winners = [
            pid for pid, w in wins_by_participant.items()
            if w == max_wins
        ]

        if len(duel_winners) != 1:
            raise ValueError(
                "Duelo empatado o ambiguo: no se puede determinar ganador"
            )

        winner_id = duel_winners[0]
        loser_ids = tuple(
            pid for pid in wins_by_participant.keys()
            if pid != winner_id
        )

        return winner_id, loser_ids
