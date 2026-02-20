"""
Legacy Event Aggregator
=======================

Notas de implementación
-----------------------

Este módulo representa la segunda capa de agregación inter-fila
dentro del pipeline legacy:

    CSV
      → Mapper
      → DTO
      → Validator
      → Normalizer
      → DuelAggregator
      → EventAggregator   ← (este módulo)
      → SeasonAggregator
      → Loader

Responsabilidades del LegacyEventAggregator:

- Consumir múltiples NormalizedDuelAggregate.
- Agrupar duelos por evento lógico.
- Ordenar duelos por secuencia.
- Determinar el event_sequence_number dentro de la temporada.
- No acceder a base de datos.
- No persistir información.
- No recalcular resultados de duelo.
- No depender del orden físico del CSV.

Ciclo de vida esperado:

    aggregator.consume(duel)
    ...
    event_aggregates = aggregator.finalize()

El método finalize() no debe modificar estado interno,
solo proyectar resultado agregado.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from services.ranking.loaders.legacy.legacy_duel_aggregator import (
    NormalizedDuelAggregate,
)
from services.ranking.loaders.legacy.row_legacy_normalizer import (
    NormalizedEventContext,
)


"""
Descripción general
-------------------

Este módulo define:

1. EventKey:
   Clave lógica que identifica un evento dentro de una temporada.

2. NormalizedEventAggregate:
   Unidad semántica que representa un evento completo ya agregado,
   incluyendo:
       - Contexto del evento.
       - Lista ordenada de duelos.
       - Número de secuencia dentro de la temporada.

3. LegacyEventAggregator:
   Clase stateful encargada de:
       - Acumular duelos.
       - Agruparlos por evento.
       - Ordenarlos.
       - Determinar su secuencia dentro de la season.
"""


# =========================
# Aggregation Models
# =========================


@dataclass(frozen=True)
class EventKey:
    """
    Clave lógica que identifica un evento dentro del sistema.

    La combinación de:
        - season_name
        - event_name

    garantiza unicidad dentro del contexto legacy.
    """
    season_name: str
    event_name: str


@dataclass(frozen=True)
class NormalizedEventAggregate:
    """
    Representa un evento completo ya agregado.

    Contiene:
        - Contexto del evento.
        - Todos los duelos asociados (ordenados).
        - Número de secuencia dentro de la temporada.
    """
    event: NormalizedEventContext
    duels: Tuple[NormalizedDuelAggregate, ...]
    event_sequence_number: int


# =========================
# Aggregator
# =========================


class LegacyEventAggregator:
    """
    Agregador de eventos a partir de duelos agregados.

    Es stateful:
        - consume() muta estado interno.
        - finalize() proyecta resultado agregado.

    No depende del orden físico del CSV.
    No accede a infraestructura.
    """

    def __init__(self) -> None:
        """
        Inicializa el estado interno.

        _events almacena:
            EventKey → lista de duelos asociados.
        """
        self._events: Dict[EventKey, List[NormalizedDuelAggregate]] = {}

    # ---------------------------------------------------------

    def consume(self, duel: NormalizedDuelAggregate) -> None:
        """
        Consume un duelo agregado y lo asigna a su evento correspondiente.

        Parámetros:
            duel: instancia de NormalizedDuelAggregate.
        """

        key = EventKey(
            season_name=duel.event.season_name,
            event_name=duel.event.event_name,
        )

        self._events.setdefault(key, []).append(duel)

    # ---------------------------------------------------------

    def finalize(self) -> Tuple[NormalizedEventAggregate, ...]:
        """
        Finaliza la agregación y construye los eventos completos.

        Reglas aplicadas:
            - Los duelos se ordenan por normal_duel_sequence_number.
            - Los eventos se ordenan por event_date.
            - El event_sequence_number se determina por orden cronológico
              dentro de la temporada.

        Retorna:
            Tupla inmutable de NormalizedEventAggregate.
        """

        # Agrupar eventos por temporada
        events_by_season: Dict[str, List[NormalizedEventAggregate]] = {}

        for key, duels in self._events.items():

            # Orden explícito de duelos
            duels_sorted = sorted(
                duels,
                key=lambda d: d.duel.normal_duel_sequence_number
            )

            event_context = duels_sorted[0].event

            # Creamos provisionalmente con sequence_number = 0
            event_aggregate = NormalizedEventAggregate(
                event=event_context,
                duels=tuple(duels_sorted),
                event_sequence_number=0,
            )

            events_by_season.setdefault(
                key.season_name,
                []
            ).append(event_aggregate)

        final_events: List[NormalizedEventAggregate] = []

        # Determinar sequence_number por season
        for events in events_by_season.values():

            # Orden cronológico explícito por fecha
            events_sorted = sorted(
                events,
                key=lambda e: e.event.event_date
            )

            for index, event in enumerate(events_sorted, start=1):

                final_events.append(
                    NormalizedEventAggregate(
                        event=event.event,
                        duels=event.duels,
                        event_sequence_number=index,
                    )
                )

        return tuple(final_events)
