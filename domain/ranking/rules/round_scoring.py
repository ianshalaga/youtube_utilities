"""
Reglas de puntuación por resultado de round.

La puntuación se basa en una barra de vida máxima de 240 puntos.
Los valores reflejan el daño efectivo infligido al rival.
"""

# Vida máxima: 240
# LY ≈ 90% de daño → 216
# LB ≈ 40% de daño → 96

ROUND_RESULT_POINTS: dict[str, int] = {
    "W": 240,    # Win
    "PW": 240,   # Perfect Win
    "D": 240,    # Draw (KO mutuo)
    "LY": 216,   # Loss Yellow (rival quedó con vida amarilla)
    "LB": 96,    # Loss Blue (rival quedó con vida azul)
    "PL": 0,     # Perfect Loss
}
