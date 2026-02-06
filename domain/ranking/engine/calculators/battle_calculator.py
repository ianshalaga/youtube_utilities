"""
Battle calculator.

Aplica un BattleEvent sobre el estado actual de las entidades
(character, player_character).
"""

from core.math.bayesian_win_rate import bayesian_win_rate
from domain.ranking.engine.factors import beating_factor, lvl_factor
from domain.ranking.engine.calculators.rating_calculator import update_rating
from domain.ranking.engine.state import CompetitiveState
from domain.ranking.models.battle_event import BattleEvent


def compute_battle_points(
    *,
    raw_points: float,
    rounds_won: int,
    rounds_draw: int,
    rounds_played: int,
    wr_self: float,
    wr_opponent: float,
    lvl_params: dict,
) -> float:
    """
    Calcula los puntos de una battle para un participante.
    No muta estado.
    """
    bf = beating_factor(
        wins=rounds_won,
        draws=rounds_draw,
        total=rounds_played,
    )

    lf = lvl_factor(
        wr_self=wr_self,
        wr_opponent=wr_opponent,
        **lvl_params,
    )

    return raw_points * bf * lf


def apply_battle_event(
    *,
    battle: BattleEvent,
    state_by_entity: dict,
    entity_key_fn,
    lvl_params: dict,
    k_rating: float,
) -> None:
    """
    Aplica un BattleEvent al estado acumulado.

    Parámetros:
    - battle: BattleEvent
    - state_by_entity: dict[key -> CompetitiveState]
    - entity_key_fn: función que extrae la key de entidad desde un participante
    - lvl_params: parámetros del lvl_factor (k, min_factor, max_factor)
    - k_rating: factor de actualización del rating
    """

    for participant in battle.participants:
        key = entity_key_fn(participant)
        state: CompetitiveState = state_by_entity.setdefault(
            key, CompetitiveState()
        )

        # ── estado previo ────────────────────────────────────
        effective_wins = state.wins + 0.5 * state.draws
        effective_losses = state.losses + 0.5 * state.draws

        wr_self = bayesian_win_rate(
            wins=effective_wins,
            losses=effective_losses,
        )

        # opponent win rate (siempre hay exactamente uno)
        opponent = next(p for p in battle.participants if p != participant)
        opp_key = entity_key_fn(opponent)
        opp_state: CompetitiveState = state_by_entity.setdefault(
            opp_key, CompetitiveState()
        )

        opp_effective_wins = opp_state.wins + 0.5 * opp_state.draws
        opp_effective_losses = opp_state.losses + 0.5 * opp_state.draws

        wr_opponent = bayesian_win_rate(
            wins=opp_effective_wins,
            losses=opp_effective_losses,
        )

        # ── calcular battle points ────────────────
        battle_points = compute_battle_points(
            raw_points=participant.raw_points,
            rounds_won=participant.rounds_won,
            rounds_draw=participant.rounds_draw,
            rounds_played=battle.rounds_played,
            wr_self=wr_self,
            wr_opponent=wr_opponent,
            lvl_params=lvl_params,
        )

        # ── actualizar estado ────────────────────────────────
        state.events_played += 1
        state.raw_score += battle_points

        if battle.is_draw:
            state.draws += 1
        elif battle.winner_player_id == participant.player_id:
            state.wins += 1
        else:
            state.losses += 1

        state.rating = update_rating(
            rating=state.rating,
            event_points=battle_points,
            k_rating=k_rating,
        )
