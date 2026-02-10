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
    Aplica un DuelEvent como UNA unidad competitiva.

    - El ganador YA debe estar resuelto en duel.winner_id
      (PLAYER: inferido desde battles)
    - Las battles solo aportan score, no wins/losses
    """

    winner_id = duel.winner_id
    loser_ids = duel.loser_ids

    winner_state = state_by_entity[winner_id]
    loser_states = [state_by_entity[lid] for lid in loser_ids]

    all_states = [winner_state, *loser_states]

    duel_points = {}

    # ─────────────────────────────────────────────
    # Calcular puntos del duelo (score input)
    # ─────────────────────────────────────────────
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

    # ─────────────────────────────────────────────
    # Aplicar resultado del duelo (UNA VEZ)
    # ─────────────────────────────────────────────

    # Ganador
    winner_state.events_played += 1
    winner_state.wins += 1
    winner_state.raw_score += duel_points[winner_id]
    winner_state.rating += duel_points[winner_id] * k_rating

    # Perdedores
    for lid in loser_ids:
        state = state_by_entity[lid]
        state.events_played += 1
        state.losses += 1
        state.raw_score += duel_points[lid]
        state.rating += duel_points[lid] * k_rating

    # ─────────────────────────────────────────────
    # Recalcular score final (consistencia)
    # ─────────────────────────────────────────────
    for state in all_states:
        state.score = compute_score(
            raw_score=state.raw_score,
            events_played=state.events_played,
        )
