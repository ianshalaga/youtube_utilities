"""
NOTAS DE IMPLEMENTACIÓN

- clamp limita un valor dentro de un rango cerrado.
- Es una función matemática pura.
- Se utiliza en el cálculo de lvl_factor.
"""


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))
