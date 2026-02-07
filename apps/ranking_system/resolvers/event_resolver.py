from sqlalchemy.orm import Session

from apps.ranking_system.resolvers.base import (
    EntityNotFoundError,
    MultipleEntitiesFoundError,
)
from services.ranking.storage.models.event import Event


class EventResolver:
    """
    Resuelve eventos (torneos, ligas, etc.).
    """

    def __init__(self, session: Session):
        self._session = session

    def by_name(
        self,
        *,
        name: str,
        season_id: int | None = None,
    ) -> int:
        query = self._session.query(Event).filter(Event.name == name)

        if season_id is not None:
            query = query.filter(Event.season_id == season_id)

        events = query.all()

        if not events:
            raise EntityNotFoundError(
                f"No existe evento con nombre '{name}'"
            )

        if len(events) > 1:
            raise MultipleEntitiesFoundError(
                f"Hay múltiples eventos llamados '{name}', "
                "especifique season_id"
            )

        return events[0].id
