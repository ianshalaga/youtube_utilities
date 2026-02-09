from sqlalchemy.orm import Session
from sqlalchemy.exc import MultipleResultsFound

from apps.ranking_system.resolvers.base import (
    EntityNotFoundError,
    MultipleEntitiesFoundError,
)


def resolve_id_by_name(
    *,
    session: Session,
    model,
    name: str | None,
    extra_filters: dict | None = None,
    label: str | None = None,
) -> int | None:
    """
    Resuelve el ID de una entidad a partir de su nombre.

    - Si name es None → devuelve None
    - Si no existe → EntityNotFoundError
    - Si no es único → MultipleEntitiesFoundError
    """
    if name is None:
        return None

    query = session.query(model).filter(model.name == name)

    if extra_filters:
        for field, value in extra_filters.items():
            query = query.filter(getattr(model, field) == value)

    try:
        entity = query.one()
    except MultipleResultsFound:
        raise MultipleEntitiesFoundError(
            f"Múltiples entidades encontradas para "
            f"{label or model.__name__} name='{name}'"
        )

    if entity is None:
        raise EntityNotFoundError(
            f"No existe {label or model.__name__} con nombre '{name}'"
        )

    return entity.id
