"""
Cálculo de puntos por duelo.
"""


def calculate_duel_points(
    battles_points: float,
    battles_beating_factor: float,
    duels_lvl_factor: float
) -> float:
    return battles_points * battles_beating_factor * duels_lvl_factor
