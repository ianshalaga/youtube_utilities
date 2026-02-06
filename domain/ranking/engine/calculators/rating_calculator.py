def update_rating(
    *,
    rating: float,
    event_points: float,
    k_rating: float = 0.02,
) -> float:
    return rating + event_points * k_rating
