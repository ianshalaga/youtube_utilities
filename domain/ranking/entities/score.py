"""
Score representa el rendimiento acumulado histórico.
No es directamente comparable entre jugadores.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Score:
    value: float
