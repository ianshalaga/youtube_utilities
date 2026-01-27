from enum import Enum


class EventType(Enum):
    TOURNAMENT = "tournament"
    LEAGUE = "league"
    TEAM_TOURNAMENT = "team_tournament"
    TOURNAMENT_SPECIAL = "tournament_special"


EVENT_TYPE_PREFIX_MAP = {
    "SSLTSE": EventType.TOURNAMENT_SPECIAL,
    "SSLTT": EventType.TEAM_TOURNAMENT,
    "SSLL": EventType.LEAGUE,
    "SSLT": EventType.TOURNAMENT,
}


def resolve_event_type(event_name: str) -> EventType:
    """
    Determina el tipo de evento a partir del nombre legacy.

    Ejemplos:
        "SSLT 1"   -> TOURNAMENT
        "SSLL 3"   -> LEAGUE
        "SSLTT 2"  -> TEAM_TOURNAMENT
        "SSLTSE 1" -> TOURNAMENT_SPECIAL
    """
    if not event_name:
        raise ValueError("Event name vacío o nulo")

    for prefix, event_type in EVENT_TYPE_PREFIX_MAP.items():
        if event_name.startswith(prefix):
            return event_type

    raise ValueError(f"Tipo de evento desconocido: {event_name}")
