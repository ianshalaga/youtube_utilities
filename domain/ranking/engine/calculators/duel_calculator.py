from domain.ranking.engine.factors import beating_factor, lvl_factor
from domain.ranking.engine.calculators.score_calculator import compute_score


def apply_duel_event(
    *,
    duel,
    state_by_entity,
    lvl_params,
    k_rating,
):
    """
    Aplica un DuelEvent como UN evento competitivo.
    """

    winner_state = state_by_entity[duel.winner_id]
    loser_states = [state_by_entity[lid] for lid in duel.loser_ids]
    all_states = [winner_state, *loser_states]

    duel_points = {}

    for participant in duel.participants:
        state = state_by_entity[participant.participant_id]

        bf = beating_factor(
            wins=participant.battles_won,
            draws=participant.battles_draw,
            total=participant.battles_played,
        )

        lf = lvl_factor(
            self_win_rate=state.win_rate,
            opponent_win_rates=[
                s.win_rate for s in all_states if s is not state
            ],
            params=lvl_params,
        )

        duel_points[participant.participant_id] = (
            participant.raw_points * bf * lf
        )

    # Ganador
    winner_state.events_played += 1
    winner_state.wins += 1
    winner_state.raw_score += duel_points[duel.winner_id]
    winner_state.rating += duel_points[duel.winner_id] * k_rating

    # Perdedores
    for lid in duel.loser_ids:
        state = state_by_entity[lid]
        state.events_played += 1
        state.losses += 1
        state.raw_score += duel_points[lid]
        state.rating += duel_points[lid] * k_rating

    # Score (consistency factor)
    for state in all_states:
        state.score = compute_score(
            raw_score=state.raw_score,
            events_played=state.events_played,
        )
