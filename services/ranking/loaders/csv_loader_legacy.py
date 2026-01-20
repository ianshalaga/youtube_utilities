from services.ranking.loaders.base import DataLoader


class CSVLoaderLegacy(DataLoader):
    """
    Loader específico para el CSV legacy (SSLEdb).
    """

    def __init__(self, csv_path, session):
        self._csv_path = csv_path
        self._session = session

    def load(self):
        """
        - Lee el CSV legacy
        - Crea Seasons, Events, Duels, Battles, Rounds
        - Mapea W / LB / LY / etc
        - Mantiene orden y secuencialidad
        """
        ...
