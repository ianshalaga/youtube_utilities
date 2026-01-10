"""
Proveedor DB de ejemplo.
"""


from services.ranking.data_provider import RankingDataProvider


class DatabaseRankingProvider(RankingDataProvider):
    def iter_duels(self):
        raise NotImplementedError("DB access pendiente")
