from dataclasses import dataclass
from typing import Iterable, Dict, Tuple
from collections import defaultdict

from domain.ranking.models.battle_event import BattleEvent
from domain.ranking.entities.ranking_entity import RankingEntity


@dataclass(frozen=True)
class DuelParticipantResult:
    participant_id: int
    battles_played: int
    battles_won: int
    battles_lost: int
    battles_draw: int


@dataclass(frozen=True)
class DuelEvent:
    duel_id: int
    competitive_level: RankingEntity
    participants: Tuple[DuelParticipantResult, ...]
    player_affiliations: Dict[int, int | None]
    battles: Tuple[BattleEvent, ...]

    @classmethod
    def from_battle_events(
        cls,
        battle_events: Iterable[BattleEvent],
        *,
        competitive_level: RankingEntity,
        player_affiliations: Dict[int, int | None],
    ) -> "DuelEvent":

        battle_events = list(battle_events)
        duel_id = battle_events[0].duel_id

        stats: Dict[int, dict] = defaultdict(
            lambda: dict(
                battles_played=0,
                battles_won=0,
                battles_lost=0,
                battles_draw=0,
            )
        )

        for battle in battle_events:
            for p in battle.participants:
                pid = p.player_id

                entity_id = (
                    pid
                    if competitive_level is RankingEntity.PLAYER
                    else player_affiliations[pid]
                )

                entry = stats[entity_id]
                entry["battles_played"] += 1

                if battle.is_draw:
                    entry["battles_draw"] += 1
                elif pid == battle.winner_player_id:
                    entry["battles_won"] += 1
                else:
                    entry["battles_lost"] += 1

        participants = tuple(
            DuelParticipantResult(participant_id=eid, **values)
            for eid, values in stats.items()
        )

        if competitive_level is RankingEntity.TEAM:
            assert all(
                pid in player_affiliations
                for battle in battle_events
                for pid in battle.participant_ids
            ), "Hay jugadores sin team asignado en duelo por equipos"

        return cls(
            duel_id=duel_id,
            competitive_level=competitive_level,
            participants=participants,
            player_affiliations=dict(player_affiliations),
            battles=tuple(battle_events),
        )
