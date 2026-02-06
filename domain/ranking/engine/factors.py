"""
Factores del sistema de ranking.

Todas las funciones aquí definidas son puras:
- no tienen estado
- no mutan argumentos
- dependen solo de sus parámetros
"""

from core.math.clamp import clamp


# ─────────────────────────────────────────────────────────────
# Beating factors
# ─────────────────────────────────────────────────────────────

def beating_factor(
    *,
    wins: int,
    draws: int,
    total: int,
    draws_weight: float = 0.5,
    epsilon: float = 0.5,
) -> float:
    """
    (wins + draws_weight * draws + ε) / (total + ε)
    """
    return (
        wins + draws_weight * draws + epsilon
    ) / (
        total + epsilon
    )


# ─────────────────────────────────────────────────────────────
# Level factors
# ─────────────────────────────────────────────────────────────

def lvl_factor(
    *,
    wr_self: float,
    wr_opponent: float,
    k: float,
    min_factor: float,
    max_factor: float,
) -> float:
    """
    lvl_factor = clamp(1 + k * (wr_opponent - wr_self))
    """
    raw = 1.0 + k * (wr_opponent - wr_self)
    return clamp(raw, min_factor, max_factor)


# ─────────────────────────────────────────────────────────────
# Consistency factor
# ─────────────────────────────────────────────────────────────

def consistency_factor(
    *,
    events_played: int,
    C: int = 10,
) -> float:
    """
    events_played / (events_played + C)
    """
    if events_played <= 0:
        return 0.0
    return events_played / (events_played + C)
