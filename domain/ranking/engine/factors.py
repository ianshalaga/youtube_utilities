"""
Cálculo de factores del sistema de ranking.
"""

from core.math.clamp import clamp


def lvl_factor(
    wr_self: float,
    wr_opponent: float,
    *,
    k: float,
    min_factor: float,
    max_factor: float
) -> float:
    """
    lvl_factor = clamp(1 + k * (wr_opponent - wr_self))
    """
    raw = 1.0 + k * (wr_opponent - wr_self)
    return clamp(raw, min_factor, max_factor)
