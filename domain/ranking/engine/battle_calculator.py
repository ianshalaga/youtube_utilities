"""
Cálculo de puntos por battle.
"""

from domain.ranking.models.battle_event import BattleEvent


def calculate_battle_points(
    battle: BattleEvent,
    rounds_beating_factor: float,
    battles_lvl_factor: float
) -> tuple[float, float]:
    winner_points = (
        battle.winner_raw_points *
        rounds_beating_factor *
        battles_lvl_factor
    )

    loser_points = (
        battle.loser_raw_points *
        rounds_beating_factor *
        battles_lvl_factor
    )

    return winner_points, loser_points
