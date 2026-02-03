"""
DuelEvent

Evento competitivo de nivel duel.
Representa un duelo completo compuesto por múltiples battles.
"""

from dataclasses import dataclass
from typing import Iterable

from domain.ranking.models.battle_event import BattleEvent


# ─────────────────────────────────────────────────────────────
# Resultados agregados dentro de un duelo
# ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DuelParticipantResult:
    """
    Resultado agregado de un jugador dentro de un duelo.
    """

    player_id: int
    battles_won: int
    battles_lost: int


# ─────────────────────────────────────────────────────────────
# DuelEvent
# ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DuelEvent:
    """
    Evento competitivo correspondiente a un duelo completo.
    """

    duel_id: int

    battles: tuple[BattleEvent, ...]

    participants: tuple[DuelParticipantResult, ...]

    winner_player_id: int
    loser_player_id: int

    # ─────────────────────────────────────────────────────────
    # Construcción
    # ─────────────────────────────────────────────────────────

    @classmethod
    def from_battle_events(
        cls,
        battle_events: Iterable[BattleEvent],
    ) -> "DuelEvent":
        """
        Construye un DuelEvent a partir de BattleEvent.
        """

        battle_events = list(battle_events)
        if not battle_events:
            raise ValueError("No se puede construir DuelEvent sin BattleEvent")

        duel_id = battle_events[0].duel_id

        stats: dict[int, dict] = {}

        for battle in battle_events:
            if battle.is_draw:
                continue  # el draw no decide el duelo

            winner = battle.winner_player_id
            loser = battle.loser_player_id

            stats.setdefault(
                winner,
                {"player_id": winner, "battles_won": 0, "battles_lost": 0},
            )
            stats.setdefault(
                loser,
                {"player_id": loser, "battles_won": 0, "battles_lost": 0},
            )

            stats[winner]["battles_won"] += 1
            stats[loser]["battles_lost"] += 1

        participants = tuple(
            DuelParticipantResult(**values)
            for values in stats.values()
        )

        if len(participants) != 2:
            raise ValueError(
                "Un DuelEvent debe tener exactamente dos participantes")

        p1, p2 = participants

        if p1.battles_won > p2.battles_won:
            winner_id = p1.player_id
            loser_id = p2.player_id
        else:
            winner_id = p2.player_id
            loser_id = p1.player_id

        return cls(
            duel_id=duel_id,
            battles=tuple(battle_events),
            participants=participants,
            winner_player_id=winner_id,
            loser_player_id=loser_id,
        )
