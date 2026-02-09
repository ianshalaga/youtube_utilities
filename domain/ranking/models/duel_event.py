from dataclasses import dataclass
from collections import defaultdict
from typing import Iterable, Tuple

from domain.ranking.entities.ranking_entity import RankingEntity
from domain.ranking.models.battle_event import BattleEvent


@dataclass(frozen=True)
class DuelParticipantResult:
    """
    Resultado agregado de un participante dentro de un duelo.
    """
    participant_id: int
    battles_played: int
    battles_won: int
    battles_lost: int
    battles_draw: int
    raw_points: float


@dataclass(frozen=True)
class DuelEvent:
    """
    Evento competitivo a nivel DUEL.
    """
    participants: Tuple[DuelParticipantResult, ...]
    battles: Tuple[BattleEvent, ...]
    competitive_level: RankingEntity

    winner_id: int
    loser_ids: Tuple[int, ...]

    @classmethod
    def from_battle_events(
        cls,
        battles: Iterable[BattleEvent],
        *,
        competitive_level: RankingEntity,
        player_affiliations: dict[int, int | None],
    ) -> "DuelEvent":

        battles = tuple(battles)
        if not battles:
            raise ValueError("No se puede construir un DuelEvent sin battles")

        stats = defaultdict(lambda: {
            "battles_played": 0,
            "battles_won": 0,
            "battles_lost": 0,
            "battles_draw": 0,
            "raw_points": 0.0,
        })

        battle_wins = defaultdict(int)

        for battle in battles:
            for player_id in battle.participant_player_ids:
                if competitive_level is RankingEntity.PLAYER:
                    entity_id = player_id
                else:
                    entity_id = player_affiliations.get(player_id)
                    if entity_id is None:
                        raise ValueError(
                            f"Player {player_id} sin team en duelo por equipos"
                        )

                stats[entity_id]["battles_played"] += 1
                stats[entity_id]["raw_points"] += (
                    battle.raw_points_by_player.get(player_id, 0.0)
                )

            if battle.is_draw:
                for entity_id in stats:
                    stats[entity_id]["battles_draw"] += 1
                continue

            winner_player = battle.winner_player_id
            winner_entity = (
                winner_player
                if competitive_level is RankingEntity.PLAYER
                else player_affiliations[winner_player]
            )

            battle_wins[winner_entity] += 1

            for entity_id in stats:
                if entity_id == winner_entity:
                    stats[entity_id]["battles_won"] += 1
                else:
                    stats[entity_id]["battles_lost"] += 1

        if not battle_wins:
            raise ValueError("Duelo inválido: ninguna battle resolvió ganador")

        max_wins = max(battle_wins.values())
        winners = [eid for eid, w in battle_wins.items() if w == max_wins]

        if len(winners) != 1:
            raise ValueError("Duelo inválido: empate de battles")

        winner_id = winners[0]
        all_entities = set(stats.keys())
        loser_ids = tuple(sorted(all_entities - {winner_id}))

        participants = tuple(
            DuelParticipantResult(
                participant_id=eid,
                battles_played=v["battles_played"],
                battles_won=v["battles_won"],
                battles_lost=v["battles_lost"],
                battles_draw=v["battles_draw"],
                raw_points=v["raw_points"],
            )
            for eid, v in stats.items()
        )

        return cls(
            participants=participants,
            battles=battles,
            competitive_level=competitive_level,
            winner_id=winner_id,
            loser_ids=loser_ids,
        )
