from dataclasses import dataclass
from collections import defaultdict
from typing import Tuple


@dataclass(frozen=True)
class BattleParticipantResult:
    player_id: int
    is_winner: bool
    is_draw: bool
    raw_points: float


@dataclass(frozen=True)
class BattleEvent:
    """
    Evento competitivo a nivel BATTLE.
    """
    battle_id: int
    duel_id: int
    participants: Tuple[BattleParticipantResult, ...]

    @property
    def is_draw(self) -> bool:
        return all(p.is_draw for p in self.participants)

    @property
    def winner_player_id(self) -> int | None:
        if self.is_draw:
            return None
        for p in self.participants:
            if p.is_winner:
                return p.player_id
        return None

    @property
    def participant_player_ids(self) -> tuple[int, ...]:
        return tuple(p.player_id for p in self.participants)

    @property
    def raw_points_by_player(self) -> dict[int, float]:
        """
        Battle-level raw_points consolidados por player.
        """
        return {p.player_id: p.raw_points for p in self.participants}

    @classmethod
    def from_round_results(
        cls,
        *,
        battle_id: int,
        duel_id: int,
        round_results,
    ):
        """
        Construye un BattleEvent a partir de RoundResult(s).

        RoundResult representa UN jugador en UN round.
        """

        if not round_results:
            raise ValueError("No se puede construir un BattleEvent sin rounds")

        raw_points = defaultdict(float)
        rounds_won = defaultdict(int)
        rounds_played = defaultdict(int)
        draws_by_round = defaultdict(int)

        for r in round_results:
            player_id = r.player_id

            # Ajusta este campo si el nombre exacto es otro
            raw_points[player_id] += r.raw_points

            rounds_played[player_id] += 1

            if r.is_draw:
                draws_by_round[player_id] += 1
            elif r.is_winner:
                rounds_won[player_id] += 1

        # Determinar resultado de la battle
        max_wins = max(rounds_won.values(), default=0)
        winners = [pid for pid, w in rounds_won.items() if w == max_wins]

        if max_wins == 0 or len(winners) != 1:
            is_draw = True
            winner_player_id = None
        else:
            is_draw = False
            winner_player_id = winners[0]

        participants = tuple(
            BattleParticipantResult(
                player_id=player_id,
                is_winner=(player_id == winner_player_id),
                is_draw=is_draw,
                raw_points=raw_points[player_id],
            )
            for player_id in raw_points.keys()
        )

        return cls(
            battle_id=battle_id,
            duel_id=duel_id,
            participants=participants,
        )
