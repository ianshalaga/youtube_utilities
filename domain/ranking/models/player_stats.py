"""
Estadísticas acumuladas de un jugador.
"""

from dataclasses import dataclass


@dataclass
class PlayerStats:
    games_played: int = 0
    wins: int = 0
    losses: int = 0
