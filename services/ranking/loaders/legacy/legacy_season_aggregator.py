"""
Legacy Season Aggregator
========================

Notas de implementación
-----------------------

Este módulo representa la tercera capa de agregación inter-fila
dentro del pipeline legacy:

    CSV
      → Mapper
      → DTO
      → Validator
      → Normalizer
      → DuelAggregator
      → EventAggregator
      → SeasonAggregator   ← (este módulo)
      → Loader

Responsabilidades del LegacySeasonAggregator:

- Consumir múltiples NormalizedEventAggregate.
- Agrupar eventos por temporada.
- Ordenar eventos por event_sequence_number.
- Derivar fechas de inicio y fin de temporada.
- No acceder a base de datos.
- No persistir información.
- No recalcular lógica de niveles inferiores.

Ciclo de vida esperado:

    aggregator.consume(event)
    ...
    season_aggregates = aggregator.finalize()

El método finalize() no debe modificar estado interno,
solo proyectar resultado agregado.
"""

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Tuple

from services.ranking.loaders.legacy.legacy_event_aggregator import (
    NormalizedEventAggregate,
)


"""
Descripción general
-------------------

Este módulo define:

1. SeasonKey:
   Clave lógica que identifica una temporada.

2. NormalizedSeasonAggregate:
   Unidad semántica que representa una temporada completa,
   incluyendo:
       - Nombre
       - Fecha de inicio
       - Fecha de fin
       - Lista ordenada de eventos

3. LegacySeasonAggregator:
   Clase stateful encargada de:
       - Acumular eventos.
       - Agruparlos por season.
       - Derivar fechas.
       - Producir aggregates inmutables.
"""


# =========================
# Aggregation Models
# =========================


@dataclass(frozen=True)
class SeasonKey:
    """
    Clave lógica que identifica una temporada dentro del sistema.
    """
    season_name: str


@dataclass(frozen=True)
class NormalizedSeasonAggregate:
    """
    Representa una temporada completa ya agregada.

    Contiene:
        - Nombre de la temporada.
        - Fecha de inicio (derivada).
        - Fecha de fin (derivada).
        - Eventos asociados (ordenados).
    """
    season_name: str
    start_date: date
    end_date: date
    events: Tuple[NormalizedEventAggregate, ...]


# =========================
# Aggregator
# =========================


class LegacySeasonAggregator:
    """
    Agregador de temporadas a partir de eventos agregados.

    Es stateful:
        - consume() muta estado interno.
        - finalize() proyecta resultado agregado.

    No depende del orden físico del CSV.
    No accede a infraestructura.
    """

    def __init__(self) -> None:
        """
        Inicializa el estado interno.

        _seasons almacena:
            SeasonKey → lista de eventos asociados.
        """
        self._seasons: Dict[SeasonKey, List[NormalizedEventAggregate]] = {}

    # ---------------------------------------------------------

    def consume(self, event: NormalizedEventAggregate) -> None:
        """
        Consume un evento agregado y lo asigna a su temporada correspondiente.

        Parámetros:
            event: instancia de NormalizedEventAggregate.
        """

        key = SeasonKey(
            season_name=event.event.season_name
        )

        self._seasons.setdefault(key, []).append(event)

    # ---------------------------------------------------------

    def finalize(self) -> Tuple[NormalizedSeasonAggregate, ...]:
        """
        Finaliza la agregación y construye las temporadas completas.

        Reglas aplicadas:
            - Los eventos se ordenan por event_sequence_number.
            - start_date se deriva como la fecha mínima de los eventos.
            - end_date se deriva como la fecha máxima de los eventos.

        Retorna:
            Tupla inmutable de NormalizedSeasonAggregate.
        """

        season_aggregates: List[NormalizedSeasonAggregate] = []

        for key, events in self._seasons.items():

            # Orden explícito por secuencia ya calculada
            events_sorted = sorted(
                events,
                key=lambda e: e.event_sequence_number
            )

            event_dates = [
                e.event.event_date for e in events_sorted
            ]

            start_date = min(event_dates)
            end_date = max(event_dates)

            season_aggregates.append(
                NormalizedSeasonAggregate(
                    season_name=key.season_name,
                    start_date=start_date,
                    end_date=end_date,
                    events=tuple(events_sorted),
                )
            )

        return tuple(season_aggregates)
