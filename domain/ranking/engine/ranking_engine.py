"""
Motor central de ranking.

Orquesta la aplicación secuencial de eventos competitivos
(BattleEvent o DuelEvent) sobre un conjunto de entidades
competitivas y produce stats finales.
"""

from typing import Iterable, Dict, Callable, TypeVar

from domain.ranking.engine.state import CompetitiveState
from domain.ranking.engine.calculators.battle_calculator import apply_battle_event
from domain.ranking.engine.calculators.duel_calculator import apply_duel_event
from domain.ranking.engine.calculators.score_calculator import compute_score
from core.math.bayesian_win_rate import bayesian_win_rate

from domain.ranking.models.battle_event import BattleEvent
from domain.ranking.models.duel_event import DuelEvent

from domain.ranking.stats.player_stats import PlayerRankingStats
from domain.ranking.stats.team_stats import TeamRankingStats
from domain.ranking.stats.character_stats import CharacterRankingStats
from domain.ranking.stats.player_character_stats import PlayerCharacterRankingStats

T = TypeVar("T")


class RankingEngine:
    """
    Orquestador del sistema de ranking.
    """

    def __init__(
        self,
        *,
        k_rating: float = 0.02,
        lvl_params: dict,
        consistency_C: int = 10,
    ):
        self._k_rating = k_rating
        self._lvl_params = lvl_params
        self._consistency_C = consistency_C

    # ─────────────────────────────────────────────────────────
    # Battle rankings
    # ─────────────────────────────────────────────────────────

    def rank_battles(
        self,
        *,
        battle_events: Iterable[BattleEvent],
        entity_key_fn: Callable,
        stats_factory: Callable[[int, CompetitiveState], T],
    ) -> Dict[int, T]:
        """
        Ranking basado en BattleEvent (characters o player_characters).
        """

        state_by_entity: Dict[int, CompetitiveState] = {}

        for battle in battle_events:
            apply_battle_event(
                battle=battle,
                state_by_entity=state_by_entity,
                entity_key_fn=entity_key_fn,
                lvl_params=self._lvl_params,
                k_rating=self._k_rating,
            )

        return self._build_stats(
            state_by_entity=state_by_entity,
            stats_factory=stats_factory,
        )

    # ─────────────────────────────────────────────────────────
    # Duel rankings
    # ─────────────────────────────────────────────────────────

    def rank_duels(
        self,
        *,
        duel_events: Iterable[DuelEvent],
        stats_factory: Callable[[int, CompetitiveState], T],
    ) -> Dict[int, T]:
        """
        Ranking basado en DuelEvent (players o teams).
        """

        state_by_entity: Dict[int, CompetitiveState] = {}

        for duel in duel_events:
            apply_duel_event(
                duel=duel,
                state_by_entity=state_by_entity,
                lvl_params=self._lvl_params,
                k_rating=self._k_rating,
            )

        return self._build_stats(
            state_by_entity=state_by_entity,
            stats_factory=stats_factory,
        )

    # ─────────────────────────────────────────────────────────
    # Construcción de stats finales
    # ─────────────────────────────────────────────────────────

    def _build_stats(
        self,
        *,
        state_by_entity: Dict[int, CompetitiveState],
        stats_factory: Callable[[int, CompetitiveState], T],
    ) -> Dict[int, T]:
        """
        Convierte CompetitiveState acumulado en stats finales.
        """

        results: Dict[int, T] = {}

        for entity_id, state in state_by_entity.items():
            eff_wins = state.wins + 0.5 * state.draws
            eff_losses = state.losses + 0.5 * state.draws

            win_rate = bayesian_win_rate(
                wins=eff_wins,
                losses=eff_losses,
            )

            score = compute_score(
                raw_score=state.raw_score,
                events_played=state.events_played,
                C=self._consistency_C,
            )

            results[entity_id] = stats_factory(
                entity_id,
                CompetitiveState(
                    events_played=state.events_played,
                    wins=state.wins,
                    losses=state.losses,
                    draws=state.draws,
                    raw_score=state.raw_score,
                    rating=state.rating,
                ),
                win_rate,
                score,
            )

        return results
