"""
NOTAS DE IMPLEMENTACIÓN

- Implementa suavizado bayesiano para win_rate.
- Evita valores extremos con pocas muestras.
"""


def bayesian_win_rate(wins: int, games: int, alpha: float = 1.0) -> float:
    """
    adjusted_wr = (wins + alpha) / (games + 2 * alpha)
    """
    if games < 0 or wins < 0:
        raise ValueError("wins y games deben ser >= 0")

    return (wins + alpha) / (games + 2 * alpha)
