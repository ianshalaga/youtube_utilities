from core.math.bayesian_win_rate import bayesian_win_rate
from domain.ranking.engine.factors import beating_factor, lvl_factor
from domain.ranking.engine.calculators.rating_calculator import update_rating
from domain.ranking.engine.calculators.battle_calculator import compute_battle_points
from domain.ranking.engine.state import CompetitiveState
from domain.ranking.models.duel_event import DuelEvent
from domain.ranking.entities.ranking_entity import RankingEntity


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

    # ── determinar ganador del duelo ────────────────────────
    winner = max(
        duel.participants,
        key=lambda p: p.battles_won
    )

    # ── definir clave competitiva ───────────────────────────
    def entity_key(p):
        return p.participant_id

    # ── aplicar duelo a cada participante ───────────────────
    for participant in duel.participants:
        key = entity_key(participant)

        state: CompetitiveState = state_by_entity.setdefault(
            key, CompetitiveState()
        )

        # ── estado previo ───────────────────────────────────
        eff_wins = state.wins + 0.5 * state.draws
        eff_losses = state.losses + 0.5 * state.draws

        wr_self = bayesian_win_rate(
            wins=eff_wins,
            losses=eff_losses,
        )

        # ── win rate promedio de oponentes ──────────────────
        opp_wrs = []

        for opp in duel.participants:
            if entity_key(opp) == key:
                continue

            opp_state = state_by_entity.setdefault(
                entity_key(opp), CompetitiveState()
            )

            opp_eff_wins = opp_state.wins + 0.5 * opp_state.draws
            opp_eff_losses = opp_state.losses + 0.5 * opp_state.draws

            opp_wrs.append(
                bayesian_win_rate(
                    wins=opp_eff_wins,
                    losses=opp_eff_losses,
                )
            )

        if not opp_wrs:
            raise RuntimeError(
                f"Duel mal formado: sin oponentes para {key}"
            )

        wr_opponent = sum(opp_wrs) / len(opp_wrs)

        # ── sumar battle points del duelo ───────────────────
        total_battle_points = 0.0

        for battle in duel.battles:
            if participant.participant_id not in battle.participant_ids:
                continue

            bp = battle.get_participant(participant.participant_id)

            total_battle_points += compute_battle_points(
                raw_points=bp.raw_points,
                rounds_won=bp.rounds_won,
                rounds_draw=bp.rounds_draw,
                rounds_played=battle.rounds_played,
                wr_self=wr_self,
                wr_opponent=wr_opponent,
                lvl_params=lvl_params,
            )

        # ── factores de duelo ───────────────────────────────
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

        # ── actualizar estado ───────────────────────────────
        state.events_played += 1
        state.raw_score += duel_points

        if participant.participant_id == winner.participant_id:
            state.wins += 1
        else:
            state.losses += 1

        state.rating = update_rating(
            rating=state.rating,
            event_points=duel_points,
            k_rating=k_rating,
        )
