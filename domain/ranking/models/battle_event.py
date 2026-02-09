from dataclasses import dataclass
from typing import Iterable

from services.ranking.storage.models.round_result import RoundResult
from domain.ranking.rules.round_scoring import ROUND_RESULT_POINTS
# from services.ranking.loaders.mappers.event_type_mapper import EventType
from services.ranking.storage.models.event_type import EventType


@dataclass(frozen=True)
class BattleParticipantResult:
    player_id: int
    game_character_id: int
    position: int
    duel_team_id: int | None

    rounds_won: int
    rounds_lost: int
    rounds_draw: int

    raw_points: int


@dataclass(frozen=True)
class BattleEvent:
    battle_id: int
    duel_id: int
    stage_id: int
    event_type: EventType

    rounds_played: int
    participants: tuple[BattleParticipantResult, ...]

    winner_player_id: int | None
    loser_player_id: int | None
    is_draw: bool

    @classmethod
    def from_round_results(
        cls,
        round_results: Iterable[RoundResult],
    ) -> "BattleEvent":

        round_results = list(round_results)
        if not round_results:
            raise ValueError("BattleEvent sin rounds")

        rr0 = round_results[0]
        battle = rr0.round.battle
        event_type = battle.duel.event.event_type

        data: dict[int, dict] = {}

        for rr in round_results:
            bp = next(
                bp for bp in rr.round.battle.battle_participants
                if bp.player_id == rr.player_id
            )

            entry = data.setdefault(
                rr.player_id,
                {
                    "player_id": rr.player_id,
                    "game_character_id": bp.game_character_id,
                    "position": bp.position,
                    "duel_team_id": bp.duel_team_id,
                    "rounds_won": 0,
                    "rounds_lost": 0,
                    "rounds_draw": 0,
                    "raw_points": 0,
                },
            )

            result = rr.result_code
            if result in ("W", "PW"):
                entry["rounds_won"] += 1
            elif result == "D":
                entry["rounds_draw"] += 1
            else:
                entry["rounds_lost"] += 1

            entry["raw_points"] += ROUND_RESULT_POINTS.get(result, 0)

        participants = tuple(
            BattleParticipantResult(**values)
            for values in data.values()
        )

        if len(participants) != 2:
            raise ValueError("BattleEvent espera exactamente 2 participantes")

        p1, p2 = participants
        if p1.rounds_won > p2.rounds_won:
            winner, loser, draw = p1.player_id, p2.player_id, False
        elif p2.rounds_won > p1.rounds_won:
            winner, loser, draw = p2.player_id, p1.player_id, False
        else:
            winner = loser = None
            draw = True

        return cls(
            battle_id=battle.id,
            duel_id=battle.duel_id,
            stage_id=battle.stage_id,
            event_type=event_type,
            rounds_played=len(round_results),
            participants=participants,
            winner_player_id=winner,
            loser_player_id=loser,
            is_draw=draw,
        )

    @property
    def participant_ids(self) -> set[int]:
        return {p.player_id for p in self.participants}

    def get_participant(self, player_id: int) -> BattleParticipantResult:
        for p in self.participants:
            if p.player_id == player_id:
                return p
        raise KeyError(
            f"Player {player_id} no participó en battle {self.battle_id}"
        )

    def with_filtered_participants(
        self,
        valid_player_ids: set[int],
    ) -> "BattleEvent":

        participants = tuple(
            p for p in self.participants
            if p.player_id in valid_player_ids
        )

        if len(participants) < 2:
            raise RuntimeError(
                f"Battle {self.battle_id} inválida tras filtrar participantes"
            )

        return BattleEvent(
            battle_id=self.battle_id,
            duel_id=self.duel_id,
            stage_id=self.stage_id,
            event_type=self.event_type,
            rounds_played=self.rounds_played,
            participants=participants,
            winner_player_id=self.winner_player_id,
            loser_player_id=self.loser_player_id,
            is_draw=self.is_draw,
        )

    @property
    def raw_points_by_player(self) -> dict[int, int]:
        """
        Devuelve los raw_points battle-level por player_id.
        """
        return {
            p.player_id: p.raw_points
            for p in self.participants
        }
