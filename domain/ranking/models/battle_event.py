"""
BattleEvent

Evento competitivo de nivel battle.
Representa una battle completa derivada de RoundResult.
"""

from dataclasses import dataclass
from typing import Iterable

from services.ranking.storage.models.round_result import RoundResult


# ─────────────────────────────────────────────────────────────
# Resultados individuales dentro de una battle
# ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class BattleParticipantResult:
    """
    Resultado agregado de un jugador dentro de una battle.
    """

    player_id: int
    game_character_id: int
    position: int

    rounds_won: int
    rounds_lost: int
    rounds_draw: int

    raw_points: int


# ─────────────────────────────────────────────────────────────
# BattleEvent
# ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class BattleEvent:
    """
    Evento competitivo correspondiente a una battle completa.
    """

    battle_id: int
    duel_id: int
    stage_id: int

    rounds_played: int

    participants: tuple[BattleParticipantResult, ...]

    winner_player_id: int | None
    loser_player_id: int | None
    is_draw: bool

    # ─────────────────────────────────────────────────────────
    # Construcción
    # ─────────────────────────────────────────────────────────

    @classmethod
    def from_round_results(
        cls,
        round_results: Iterable[RoundResult],
    ) -> "BattleEvent":
        """
        Construye un BattleEvent a partir de RoundResult ORM.
        """

        round_results = list(round_results)
        if not round_results:
            raise ValueError(
                "No se puede construir BattleEvent sin RoundResult")

        first_rr = round_results[0]
        battle = first_rr.round.battle

        data: dict[int, dict] = {}

        for rr in round_results:
            bp = next(
                bp
                for bp in rr.round.battle.battle_participants
                if bp.player_id == rr.player_id
            )

            entry = data.setdefault(
                rr.player_id,
                {
                    "player_id": rr.player_id,
                    "game_character_id": bp.game_character_id,
                    "position": bp.position,
                    "rounds_won": 0,
                    "rounds_lost": 0,
                    "rounds_draw": 0,
                    "raw_points": 0,
                },
            )

            # Interpretación del resultado del round
            if rr.result_code in ("W", "PW"):
                entry["rounds_won"] += 1
                entry["raw_points"] += 240

            elif rr.result_code == "D":
                entry["rounds_draw"] += 1
                entry["raw_points"] += 240

            elif rr.result_code in ("LB", "LY"):
                entry["rounds_lost"] += 1

            elif rr.result_code == "PL":
                entry["rounds_lost"] += 1
                # 0 puntos

        participants = tuple(
            BattleParticipantResult(**values)
            for values in data.values()
        )

        # Determinar ganador / perdedor / empate
        p1, p2 = participants

        if p1.rounds_won > p2.rounds_won:
            winner_id = p1.player_id
            loser_id = p2.player_id
            is_draw = False
        elif p2.rounds_won > p1.rounds_won:
            winner_id = p2.player_id
            loser_id = p1.player_id
            is_draw = False
        else:
            winner_id = None
            loser_id = None
            is_draw = True

        return cls(
            battle_id=battle.id,
            duel_id=battle.duel_id,
            stage_id=battle.stage_id,
            rounds_played=len(round_results),
            participants=participants,
            winner_player_id=winner_id,
            loser_player_id=loser_id,
            is_draw=is_draw,
        )
