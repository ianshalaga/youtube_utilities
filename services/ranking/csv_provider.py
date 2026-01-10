"""
Proveedor CSV de ejemplo.
"""


from services.ranking.data_provider import RankingDataProvider


class CsvRankingProvider(RankingDataProvider):
    def __init__(self, csv_path):
        self._csv_path = csv_path

    def iter_duels(self):
        raise NotImplementedError("CSV parsing pendiente")
