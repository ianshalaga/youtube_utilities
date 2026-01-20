from services.ranking.loaders.base import DataLoader


class CSVLoaderV2(DataLoader):
    """
    Loader para el formato round-based definitivo.
    """

    def load(self):
        """
        Cada fila = un Round
        """
        ...
