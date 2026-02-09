from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
from typing import Iterable

from domain.ranking.entities import RankingEntity
from domain.ranking.models.battle_event import BattleEvent


@dataclass(frozen=True)
class DuelParticipantResult:
    """
    Resultado agregado de un participante dentro de un duelo.

    NOTA SEMÁNTICA:
    - participant_id representa la entidad competitiva:
        - PLAYER  -> player_id
        - TEAM    -> team_id
    - battles_* son métricas internas del duelo.
      NO representan resultados competitivos finales.
    """
    participant_id: int
    battles_played: int
    battles_won: int
    battles_lost: int
    battles_draw: int


@dataclass(frozen=True)
class DuelEvent:
    """
    Evento competitivo a nivel DUEL.

    CONTRATO:
    - Aplica exclusivamente a entidades duel-level (PLAYER, TEAM).
    - Un duelo tiene exactamente UN ganador.
    - Puede tener uno o más perdedores.
    - No existen empates de duelo.
    - Las battles son información interna.
    """

    participants: tuple[DuelParticipantResult, ...]
    battles: tuple[BattleEvent, ...]
    competitive_level: RankingEntity

    # Resultado explícito del duelo (nivel competitivo)
    winner_id: int
    loser_ids: tuple[int, ...]

    # ──────────────────────────────────────────────────────────────
    # Construcción
    # ──────────────────────────────────────────────────────────────

    @classmethod
    def from_battle_events(
        cls,
        battles: Iterable[BattleEvent],
        *,
        competitive_level: RankingEntity,
        player_affiliations: dict[int, int | None],
    ) -> DuelEvent:
        """
        Construye un DuelEvent a partir de BattleEvents.

        RESPONSABILIDAD:
        - Agregar información battle-level.
        - Resolver explícitamente el resultado del duelo.
        - NO inferir semántica aguas abajo.
        """

        battles = tuple(battles)
        if not battles:
            raise ValueError("No se puede construir un DuelEvent sin battles")

        # ──────────────────────────────────────────────────────────
        # Inicializar stats internas por participante
        # ──────────────────────────────────────────────────────────

        stats: dict[int, dict[str, int]] = defaultdict(
            lambda: {
                "battles_played": 0,
                "battles_won": 0,
                "battles_lost": 0,
                "battles_draw": 0,
            }
        )

        # Conteo de battles ganadas (para resolver el duelo)
        battle_wins: dict[int, int] = defaultdict(int)

        # ──────────────────────────────────────────────────────────
        # Procesar battles
        # ──────────────────────────────────────────────────────────

        for battle in battles:
            # Resolver participantes de la battle a nivel competitivo
            participant_entities: list[int] = []

            for pid in battle.participant_player_ids:
                if competitive_level is RankingEntity.PLAYER:
                    participant_entities.append(pid)
                else:
                    team_id = player_affiliations.get(pid)
                    if team_id is None:
                        raise ValueError(
                            f"Player {pid} no tiene team asignado en duelo por equipos"
                        )
                    participant_entities.append(team_id)

            # Actualizar battles_played
            for entity_id in participant_entities:
                stats[entity_id]["battles_played"] += 1

            # Resolver resultado de la battle
            if battle.is_draw:
                for entity_id in participant_entities:
                    stats[entity_id]["battles_draw"] += 1
                continue

            winner_player_id = battle.winner_player_id

            if competitive_level is RankingEntity.PLAYER:
                winner_entity_id = winner_player_id
            else:
                winner_entity_id = player_affiliations[winner_player_id]

            battle_wins[winner_entity_id] += 1

            for entity_id in participant_entities:
                if entity_id == winner_entity_id:
                    stats[entity_id]["battles_won"] += 1
                else:
                    stats[entity_id]["battles_lost"] += 1

        # ──────────────────────────────────────────────────────────
        # Resolver ganador del duelo
        # ──────────────────────────────────────────────────────────

        if not battle_wins:
            raise ValueError("Duelo inválido: ninguna battle resolvió ganador")

        # Determinar máximo de battles ganadas
        max_wins = max(battle_wins.values())
        winners = [eid for eid, w in battle_wins.items() if w == max_wins]

        if len(winners) != 1:
            raise ValueError(
                "Duelo inválido: empate de battles a nivel duelo"
            )

        winner_id = winners[0]

        # Todos los demás participantes son perdedores
        all_participants = set(stats.keys())
        loser_ids = tuple(sorted(all_participants - {winner_id}))

        if not loser_ids:
            raise ValueError("Duelo inválido: no hay perdedores")

        # ──────────────────────────────────────────────────────────
        # Construir resultados finales
        # ──────────────────────────────────────────────────────────

        participants = tuple(
            DuelParticipantResult(
                participant_id=entity_id,
                battles_played=values["battles_played"],
                battles_won=values["battles_won"],
                battles_lost=values["battles_lost"],
                battles_draw=values["battles_draw"],
            )
            for entity_id, values in stats.items()
        )

        return cls(
            participants=participants,
            battles=battles,
            competitive_level=competitive_level,
            winner_id=winner_id,
            loser_ids=loser_ids,
        )
