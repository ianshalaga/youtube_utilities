from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class RowLegacyDTO:
    '''
    Es un objeto tipado, normalizado y estructurado.

    Responsabilidad:
    - Convertir strings en tipos reales.
    - Convertir enteros.
    - Convertir fechas.
    - Agrupar rounds en listas.
    - Resolver team_duel_sequence.
    - Inferir event_type.
    - Representar una fila lista para validación.

    El DTO es el resultado del parsing.
    '''
    pass
