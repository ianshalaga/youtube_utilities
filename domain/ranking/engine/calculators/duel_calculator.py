"""
Duel calculator.

Aplica un DuelEvent sobre el estado acumulado de las entidades
competitivas (players o teams).

Un DuelEvent representa SIEMPRE un resultado definitivo:
- un ganador
- uno o más perdedores
- nunca hay empate
"""

from core.math.bayesian_win_rate import bayesian_win_rate
from domain.ranking.engine.factors import beating_factor, lvl_factor
from domain.ranking.engine.calculators.rating_calculator import update_rating
from domain.ranking.engine.calculators.battle_calculator import compute_battle_points
from domain.ranking.engine.state import CompetitiveState
from domain.ranking.models.duel_event import DuelEvent


def apply_duel_event(
    *,
    duel: DuelEvent,
    state_by_entity: dict,
    lvl_params: dict,
    k_rating: float,
) -> None:
    """
    Aplica un DuelEvent al estado acumulado.

    El estado se actualiza UNA vez por duelo:
    - ganador: win += 1
    - resto: loss += 1
    """

    # ─────────────────────────────────────────────────────────
    # Determinar ganador del duelo
    # ─────────────────────────────────────────────────────────

    winner = max(
        duel.participants,
        key=lambda p: p.battles_won
    )

    # ─────────────────────────────────────────────────────────
    # Aplicar duelo a cada participante
    # ─────────────────────────────────────────────────────────

    for participant in duel.participants:
        key = participant.participant_id
        state: CompetitiveState = state_by_entity.setdefault(
            key, CompetitiveState()
        )

        # ── estado previo (ANTES del duelo) ──────────────────
        eff_wins = state.wins + 0.5 * state.draws
        eff_losses = state.losses + 0.5 * state.draws

        wr_self = bayesian_win_rate(
            wins=eff_wins,
            losses=eff_losses,
        )

        # win rate promedio de oponentes
        opp_wrs = []
        for opp in duel.participants:
            if opp.participant_id == key:
                continue

            opp_state = state_by_entity.setdefault(
                opp.participant_id, CompetitiveState()
            )

            opp_eff_wins = opp_state.wins + 0.5 * opp_state.draws
            opp_eff_losses = opp_state.losses + 0.5 * opp_state.draws

            opp_wrs.append(
                bayesian_win_rate(
                    wins=opp_eff_wins,
                    losses=opp_eff_losses,
                )
            )

        wr_opponent = sum(opp_wrs) / len(opp_wrs)

        # ─────────────────────────────────────────────────────
        # Sumar battle points del duelo
        # ─────────────────────────────────────────────────────

        total_battle_points = 0.0

        for battle in duel.battles:
            if key not in battle.participant_ids:
                continue

            bp = battle.get_participant(key)

            total_battle_points += compute_battle_points(
                raw_points=bp.raw_points,
                rounds_won=bp.rounds_won,
                rounds_draw=bp.rounds_draw,
                rounds_played=battle.rounds_played,
                wr_self=wr_self,
                wr_opponent=wr_opponent,
                lvl_params=lvl_params,
            )

        # ─────────────────────────────────────────────────────
        # Factores de duelo
        # ─────────────────────────────────────────────────────

        bf = beating_factor(
            wins=participant.battles_won,
            draws=participant.battles_draw,
            total=participant.battles_played,
        )

        lf = lvl_factor(
            wr_self=wr_self,
            wr_opponent=wr_opponent,
            **lvl_params,
        )

        duel_points = total_battle_points * bf * lf

        # ─────────────────────────────────────────────────────
        # Actualizar estado (UNA vez por duelo)
        # ─────────────────────────────────────────────────────

        state.events_played += 1
        state.raw_score += duel_points

        if participant.participant_id == winner.participant_id:
            state.wins += 1
        else:
            state.losses += 1

        # En duelos NO hay draws
        state.rating = update_rating(
            rating=state.rating,
            event_points=duel_points,
            k_rating=k_rating,
        )
