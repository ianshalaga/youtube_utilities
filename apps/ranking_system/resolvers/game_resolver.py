# apps/ranking_system/resolvers/game_resolver.py

from sqlalchemy.orm import Session

from apps.ranking_system.resolvers.base import (
    EntityNotFoundError,
    MultipleEntitiesFoundError,
)

from services.ranking.storage.models.game import Game
from services.ranking.storage.models.game_version_platform import GameVersionPlatform
from services.ranking.storage.models.platform import Platform


class GameResolver:
    """
    Resuelve juegos y combinaciones juego + versión + plataforma.
    """

    def __init__(self, session: Session):
        self._session = session

    # ─────────────────────────────────────────────────────────
    # Game
    # ─────────────────────────────────────────────────────────

    def game_by_name(self, name: str) -> int:
        game = (
            self._session.query(Game)
            .filter(Game.name == name)
            .one_or_none()
        )

        if game is None:
            raise EntityNotFoundError(
                f"No existe juego con nombre '{name}'"
            )

        return game.id

    # ─────────────────────────────────────────────────────────
    # Game + Version + Platform
    # ─────────────────────────────────────────────────────────

    def game_version_platform(
        self,
        *,
        game_name: str,
        platform_name: str,
        version: str,
    ) -> int:
        """
        Resuelve el game_version_platform_id a partir de
        (game, platform, version).
        """

        query = (
            self._session.query(GameVersionPlatform)
            .join(Game)
            .join(Platform)
            .filter(Game.name == game_name)
            .filter(Platform.name == platform_name)
            .filter(GameVersionPlatform.version == version)
        )

        results = query.all()

        if not results:
            raise EntityNotFoundError(
                f"No existe combinación "
                f"game='{game_name}', "
                f"platform='{platform_name}', "
                f"version='{version}'"
            )

        if len(results) > 1:
            raise MultipleEntitiesFoundError(
                f"Múltiples combinaciones encontradas para "
                f"game='{game_name}', "
                f"platform='{platform_name}', "
                f"version='{version}'"
            )

        return results[0].id
