from domain.ranking.engine.factors import (
    beating_factor,
    lvl_factor,
)
from domain.ranking.engine.calculators.score_calculator import compute_score


def apply_duel_event(
    *,
    duel,
    state_by_entity,
    lvl_params,
    k_rating,
):
    """
    Aplica un DuelEvent a los estados competitivos.

    CONTRATO:
    - Un DuelEvent equivale a UN evento competitivo.
    - El ganador y perdedores vienen dados explícitamente.
    - Las battles solo aportan puntos (score / rating).
    """

    # ──────────────────────────────────────────────────────────
    # Resolver estados
    # ──────────────────────────────────────────────────────────

    winner_state = state_by_entity[duel.winner_id]
    loser_states = [state_by_entity[lid] for lid in duel.loser_ids]

    # Todos los participantes (ganador + perdedores)
    participant_states = [winner_state, *loser_states]

    # ──────────────────────────────────────────────────────────
    # Calcular duel_points para cada participante
    # ──────────────────────────────────────────────────────────

    duel_points_by_entity = {}

    for participant in duel.participants:
        state = state_by_entity[participant.participant_id]

        # Sumar puntos de battles (battle-level)
        battle_points = 0.0
        for battle in duel.battles:
            battle_points += battle.raw_points_by_player.get(
                participant.participant_id,
                0.0,
            )

        # battles_beating_factor (proporción de éxito en battles)
        bf = beating_factor(
            wins=participant.battles_won,
            draws=participant.battles_draw,
            total=participant.battles_played,
        )

        # duel-level lvl_factor
        lf = lvl_factor(
            self_win_rate=state.win_rate,
            opponent_win_rates=[
                s.win_rate for s in participant_states
                if s is not state
            ],
            params=lvl_params,
        )

        duel_points = battle_points * bf * lf
        duel_points_by_entity[participant.participant_id] = duel_points

    # ──────────────────────────────────────────────────────────
    # Actualizar estados (UNA VEZ POR DUELO)
    # ──────────────────────────────────────────────────────────

    # Ganador
    winner_state.events_played += 1
    winner_state.wins += 1
    winner_state.raw_score += duel_points_by_entity[duel.winner_id]
    winner_state.rating += duel_points_by_entity[duel.winner_id] * k_rating

    # Perdedores
    for loser_id in duel.loser_ids:
        loser_state = state_by_entity[loser_id]
        loser_state.events_played += 1
        loser_state.losses += 1
        loser_state.raw_score += duel_points_by_entity[loser_id]
        loser_state.rating += duel_points_by_entity[loser_id] * k_rating

    # ──────────────────────────────────────────────────────────
    # Score (consistency factor)
    # ──────────────────────────────────────────────────────────

    for state in participant_states:
        state.score = compute_score(
            raw_score=state.raw_score,
            events_played=state.events_played,
        )
