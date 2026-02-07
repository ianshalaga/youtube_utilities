# apps/ranking_system/resolvers/season_resolver.py

from sqlalchemy.orm import Session

from apps.ranking_system.resolvers.base import EntityNotFoundError
from services.ranking.storage.models.season import Season


class SeasonResolver:
    """
    Resuelve seasons desde información humana.
    """

    def __init__(self, session: Session):
        self._session = session

    def by_name(self, name: str | None) -> int | None:
        """
        Devuelve el season_id correspondiente al nombre.

        - Si name es None, devuelve None (no se filtra).
        - Si name no existe, lanza EntityNotFoundError.
        """
        if name is None:
            return None

        season = (
            self._session.query(Season)
            .filter(Season.name == name)
            .one_or_none()
        )

        if season is None:
            raise EntityNotFoundError(
                f"No existe season con nombre '{name}'"
            )

        return season.id
