# apps/ranking_system/resolvers/platform_resolver.py

from sqlalchemy.orm import Session

from apps.ranking_system.resolvers.base import EntityNotFoundError
from services.ranking.storage.models.platform import Platform


class PlatformResolver:
    """
    Resuelve plataformas (PC, PS5, Xbox, etc.).
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

        platform = (
            self._session.query(Platform)
            .filter(Platform.name == name)
            .one_or_none()
        )

        if platform is None:
            raise EntityNotFoundError(
                f"No existe plataforma con nombre '{name}'"
            )

        return platform.id
