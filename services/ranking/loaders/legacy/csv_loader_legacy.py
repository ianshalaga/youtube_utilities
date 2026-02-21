"""
CSV Legacy Loader
=================

Notas de implementación
-----------------------

Este módulo representa la capa final del pipeline legacy.

Responsabilidades:

- Leer archivo CSV.
- Orquestar pipeline completo:
    Mapper → DTO → Validator → Normalizer
- Ejecutar agregación:
    Duel → Event → Season
- Persistir aggregates en base de datos.

No:
- Deriva lógica de dominio.
- Recalcula resultados.
- Contiene reglas de negocio.
"""

import csv
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import Session

from services.ranking.loaders.legacy.row_legacy_mapper import RowLegacyMapper
from services.ranking.loaders.legacy.row_legacy_dto import RowLegacyDTO
from services.ranking.loaders.legacy.row_legacy_validator import RowLegacyValidator
from services.ranking.loaders.legacy.row_legacy_normalizer import RowLegacyNormalizer

from services.ranking.loaders.legacy.legacy_duel_aggregator import LegacyDuelAggregator
from services.ranking.loaders.legacy.legacy_event_aggregator import LegacyEventAggregator
from services.ranking.loaders.legacy.legacy_season_aggregator import LegacySeasonAggregator
from services.ranking.loaders.legacy.legacy_aggregate_persistence import LegacyAggregatePersistence


class CsvLegacyLoader:
    """
    Orquestador principal de carga legacy.

    Encapsula:
    - Pipeline estructural.
    - Agregación inter-fila.
    - Persistencia final.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # ---------------------------------------------------------

    def load(self, file_path: str | Path) -> None:
        """
        Ejecuta el proceso completo de carga.

        Lanza excepción si alguna etapa falla.
        La transacción debe manejarse externamente
        o envolver esta llamada.
        """

        duel_agg = LegacyDuelAggregator()
        event_agg = LegacyEventAggregator()
        season_agg = LegacySeasonAggregator()

        # ------------------------------
        # Phase 1: Ingestion
        # ------------------------------

        for row_dict in self._read_csv(file_path):

            mapper = RowLegacyMapper(row_dict)
            dto = RowLegacyDTO.from_mapper(mapper)
            RowLegacyValidator.validate(dto)
            battle = RowLegacyNormalizer.normalize(dto)

            duel_agg.consume(battle)

        # ------------------------------
        # Phase 2: Aggregation
        # ------------------------------

        duels = duel_agg.finalize()

        for duel in duels:
            event_agg.consume(duel)

        events = event_agg.finalize()

        for event in events:
            season_agg.consume(event)

        seasons = season_agg.finalize()

        # ------------------------------
        # Phase 3: Persistence
        # ------------------------------

        persistence = LegacyAggregatePersistence(self._session)
        persistence.persist(seasons)

        self._session.commit()

    # ---------------------------------------------------------

    @staticmethod
    def _read_csv(file_path: str | Path) -> Iterable[dict[str, str]]:
        """
        Lee el CSV y produce diccionarios por fila.
        """

        with open(file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                yield row
