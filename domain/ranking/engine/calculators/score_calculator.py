from domain.ranking.engine.factors import consistency_factor


def compute_score(
    *,
    raw_score: float,
    events_played: int,
    C: int = 10,
) -> float:
    return raw_score * consistency_factor(
        events_played=events_played,
        C=C,
    )
