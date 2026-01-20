import csv
from pathlib import Path

from services.ranking.storage.models import (
    Season, Event, Duel, Battle, Round, RoundResult
)


class CSVExporterV2:
    """
    Exporta datos persistidos a formato CSV v2 (round-based).
    """

    HEADERS = [
        "season",
        "event_order",
        "event_name",
        "event_date",
        "event_playlist",
        "event_bracket",
        "region",
        "platform",
        "game",
        "version",
        "duel_order",
        "duel_type",
        "duel_video",
        "combat_order",
        "player_1",
        "character_1",
        "p1_round_result",
        "p1_country",
        "player_2",
        "character_2",
        "p2_round_result",
        "p2_country",
        "stage",
        "p1_team",
        "p2_team",
    ]

    def __init__(self, session, *, season_id=None, event_id=None):
        self._session = session
        self._season_id = season_id
        self._event_id = event_id

    def export(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)

            for row in self._iter_rows():
                writer.writerow(row)

    def _iter_rows(self):
        """
        Itera la DB y reconstruye filas CSV v2.
        """
        # aquí iría la lógica ORM que aplana
        # Event → Duel → Battle → Round → Results
        yield from ()
