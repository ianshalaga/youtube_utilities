from dataclasses import dataclass
from typing import Dict, Iterable

from domain.ranking.enums.round_result_code import RoundResultCode
from domain.ranking.rules.round_scoring import ROUND_RESULT_POINTS


@dataclass(frozen=True)
class BattleRound:
    """
    Resultado de UN jugador en UN round.
    """
    player_id: int
    result_code: RoundResultCode


@dataclass(frozen=True)
class BattleEvent:
    battle_id: int
    duel_id: int
    participants: tuple[int, ...]
    raw_points_by_participant: Dict[int, int]

    @classmethod
    def from_round_results(
        cls,
        *,
        battle_id: int,
        duel_id: int,
        round_results: Iterable,
    ) -> "BattleEvent":

        raw_points: dict[int, int] = {}
        participants: set[int] = set()

        for r in round_results:
            player_id = r.player_id
            participants.add(player_id)

            result_code: RoundResultCode = r.result_code
            code_value = result_code.value

            if code_value not in ROUND_RESULT_POINTS:
                raise ValueError(
                    f"RoundResultCode no soportado: {result_code}"
                )

            points = ROUND_RESULT_POINTS[code_value]
            raw_points[player_id] = raw_points.get(player_id, 0) + points

        if len(participants) < 2:
            raise ValueError(
                f"Battle inválida {battle_id}: menos de 2 participantes"
            )

        return cls(
            battle_id=battle_id,
            duel_id=duel_id,
            participants=tuple(sorted(participants)),
            raw_points_by_participant=raw_points,
        )
