from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

from domain.ranking.enums.round_result_code import RoundResultCode
from domain.ranking.rules.round_scoring import ROUND_RESULT_POINTS


@dataclass(frozen=True)
class BattleEvent:
    """
    Evento competitivo a nivel BATTLE.

    - El ganador de la battle se decide por rounds ganados
    - raw_points se usan solo para score
    - NO decide resultados de duelo
    """
    battle_id: int
    duel_id: int
    participants: Tuple[int, ...]
    rounds_won_by_participant: Dict[int, int]
    raw_points_by_participant: Dict[int, int]

    @classmethod
    def from_round_results(
        cls,
        *,
        battle_id: int,
        duel_id: int,
        round_results: Iterable,
    ) -> "BattleEvent":

        participants: set[int] = set()
        rounds_won: dict[int, int] = {}
        raw_points: dict[int, int] = {}

        for r in round_results:
            player_id = r.player_id
            participants.add(player_id)

            # Convertir string DB -> Enum dominio
            try:
                code = RoundResultCode(r.result_code)
            except ValueError:
                raise ValueError(
                    f"RoundResultCode inválido: {r.result_code}"
                )

            # ── Rounds ganados (define ganador de la battle)
            if code in (RoundResultCode.W, RoundResultCode.PW):
                rounds_won[player_id] = rounds_won.get(player_id, 0) + 1

            # ── Raw points (define score)
            code_value = code.value
            if code_value not in ROUND_RESULT_POINTS:
                raise ValueError(
                    f"RoundResultCode no soportado: {code}"
                )

            raw_points[player_id] = (
                raw_points.get(player_id, 0)
                + ROUND_RESULT_POINTS[code_value]
            )

        if len(participants) < 2:
            raise ValueError(
                f"Battle inválida {battle_id}: menos de 2 participantes"
            )

        return cls(
            battle_id=battle_id,
            duel_id=duel_id,
            participants=tuple(sorted(participants)),
            rounds_won_by_participant=rounds_won,
            raw_points_by_participant=raw_points,
        )
