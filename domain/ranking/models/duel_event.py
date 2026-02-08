"""
DuelEvent

Evento competitivo de nivel duel.

Representa un duelo completo que puede ser:
- individual (player vs player, FFA)
- por equipos (team vs team, con rotación de jugadores)

El DuelEvent NO calcula puntos ni rankings.
Solo agrega hechos competitivos derivados de BattleEvent.
"""

from dataclasses import dataclass
from typing import Iterable, Literal, Dict, Tuple
from collections import defaultdict

from domain.ranking.models.battle_event import BattleEvent
from domain.ranking.entities.ranking_entity import RankingEntity


# ─────────────────────────────────────────────────────────────
# Resultado agregado por entidad competitiva
# ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DuelParticipantResult:
    """
    Resultado agregado de una entidad competitiva dentro de un duelo.

    La entidad competitiva puede ser:
    - un jugador (participant_type = "player")
    - un equipo  (participant_type = "team")
    """
    participant_id: int

    battles_played: int
    battles_won: int
    battles_lost: int
    battles_draw: int


# ─────────────────────────────────────────────────────────────
# DuelEvent
# ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DuelEvent:
    """
    Evento competitivo correspondiente a un duelo completo.
    """

    duel_id: int

    # Nivel competitivo del duelo:
    # - "player" → duelos individuales
    # - "team"   → duelos por equipos
    competitive_level: RankingEntity

    # Resultados agregados por entidad competitiva
    participants: Tuple[DuelParticipantResult, ...]

    # Relación jugador → entidad competitiva (player_id → player_id o team_id)
    # En duelos individuales: player_id → player_id
    # En duelos por equipos:  player_id → team_id
    player_affiliations: Dict[int, int]

    # ─────────────────────────────────────────────────────────
    # Construcción
    # ─────────────────────────────────────────────────────────

    @classmethod
    def from_battle_events(
        cls,
        battle_events: Iterable[BattleEvent],
        *,
        competitive_level: RankingEntity,
        player_affiliations: Dict[int, int],
    ) -> "DuelEvent":

        battle_events = list(battle_events)
        if not battle_events:
            raise ValueError("No se puede construir DuelEvent sin BattleEvent")

        duel_id = battle_events[0].duel_id

        stats: Dict[int, dict] = defaultdict(
            lambda: {
                "battles_played": 0,
                "battles_won": 0,
                "battles_lost": 0,
                "battles_draw": 0,
            }
        )

        for battle in battle_events:
            for participant in battle.participants:
                player_id = participant.player_id

                if player_id not in player_affiliations:
                    raise ValueError(
                        f"Player {player_id} no tiene afiliación definida para el duelo"
                    )

                if competitive_level is RankingEntity.PLAYER:
                    entity_id = player_id

                elif competitive_level is RankingEntity.TEAM:
                    entity_id = player_affiliations[player_id]
                    if entity_id is None:
                        raise ValueError(
                            f"Duelo por equipos con player {player_id} sin team asignado"
                        )
                else:
                    raise ValueError(
                        f"Competitive level no soportado: {competitive_level}"
                    )

                entry = stats[entity_id]

                entry["battles_played"] += 1

                if battle.is_draw:
                    entry["battles_draw"] += 1
                elif participant.player_id == battle.winner_player_id:
                    entry["battles_won"] += 1
                else:
                    entry["battles_lost"] += 1

        participants = tuple(
            DuelParticipantResult(
                participant_id=entity_id,
                battles_played=data["battles_played"],
                battles_won=data["battles_won"],
                battles_lost=data["battles_lost"],
                battles_draw=data["battles_draw"],
            )
            for entity_id, data in stats.items()
        )

        return cls(
            duel_id=duel_id,
            competitive_level=competitive_level,
            participants=participants,
            player_affiliations=dict(player_affiliations),
        )
