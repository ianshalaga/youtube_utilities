from services.ranking.providers.base import DataProvider


class DBProvider(DataProvider):
    """
    Proveedor de datos desde la base SQL.
    """

    def iter_duels(self, *, season=None, platform=None, country=None):
        """
        Devuelve duelos ya persistidos y ordenados.
        """
        ...

    def iter_battles(self, *, character=None, game_version=None):
        ...
