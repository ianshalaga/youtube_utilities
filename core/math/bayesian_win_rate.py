"""
NOTAS DE IMPLEMENTACIÓN

- Implementa suavizado bayesiano para win_rate.
- Evita valores extremos con pocas muestras.
"""


def bayesian_win_rate(
    wins: float,
    losses: float,
    *,
    prior_wins: float = 1.0,
    prior_losses: float = 1.0,
) -> float:
    return (wins + prior_wins) / (wins + losses + prior_wins + prior_losses)
