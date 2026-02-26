"""
Legacy Duel Aggregator
======================

Notas de implementación
-----------------------

Este módulo representa la primera capa de agregación inter-fila
dentro del pipeline legacy:

    CSV
      → Mapper
      → DTO
      → Validator
      → Normalizer
      → DuelAggregator   ← (este módulo)
      → EventAggregator
      → SeasonAggregator
      → Loader

Responsabilidades del LegacyDuelAggregator:

- Consumir múltiples NormalizedBattleAggregate.
- Agrupar battles por clave lógica de duelo.
- Derivar el ganador del duelo según reglas del dominio.
- Ignorar battles empatadas.
- Garantizar que solo exista un ganador.
- No acceder a base de datos.
- No persistir información.
- No depender del orden físico del CSV.

El ciclo de vida esperado es:

    aggregator.consume(battle)
    ...
    duel_aggregates = aggregator.finalize()

El método finalize() no debe modificar estado interno,
solo proyectar el resultado agregado.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

from services.ranking.loaders.legacy.row_legacy_normalizer import (
    NormalizedBattleAggregate,
    NormalizedEventContext,
    NormalizedDuelContext,
)


"""
Descripción general
-------------------

Este módulo define:

1. DuelKey:
   Clave lógica que identifica de forma única un duelo dentro
   de un evento y temporada.

2. NormalizedDuelAggregate:
   Unidad semántica que representa un duelo completo ya agregado,
   incluyendo:
       - Contexto del evento
       - Contexto del duelo
       - Lista ordenada de battles
       - Ganador único
       - Lista de perdedores

3. LegacyDuelAggregator:
   Clase stateful encargada de:
       - Acumular battles normalizadas.
       - Agruparlas por duelo.
       - Calcular ganador del duelo.
       - Producir aggregates inmutables.
"""


# =========================
# Aggregation Models
# =========================


@dataclass(frozen=True)
class DuelKey:
    """
    Clave lógica que identifica un duelo dentro del sistema.

    La combinación de:
        - season_name
        - event_name
        - duel_sequence_number

    garantiza unicidad en el contexto legacy.
    """
    season_name: str
    event_name: str
    duel_sequence_number: int


@dataclass(frozen=True)
class NormalizedDuelAggregate:
    """
    Representa un duelo completo ya agregado.

    Contiene:
        - Contexto del evento.
        - Contexto del duelo.
        - Todas las battles que lo componen (ordenadas).
        - Nombre del jugador ganador.
        - Nombres de los jugadores perdedores.
    """
    event: NormalizedEventContext
    duel: NormalizedDuelContext
    battles: Tuple[NormalizedBattleAggregate, ...]
    winner_player_name: str
    loser_player_names: Tuple[str, ...]
    winner_team_name: Optional[str]
    loser_team_names: Tuple[str, ...]


# =========================
# Aggregator
# =========================


class LegacyDuelAggregator:
    """
    Agregador de duelos a partir de battles normalizadas.

    Es stateful:
        - consume() muta estado interno.
        - finalize() proyecta resultado agregado.

    No depende del orden físico del CSV.
    No accede a infraestructura.
    """

    def __init__(self) -> None:
        """
        Inicializa el estado interno del agregador.

        _duels almacena:
            DuelKey → lista de battles asociadas.
        """
        self._duels: Dict[DuelKey, List[NormalizedBattleAggregate]] = {}

    # ---------------------------------------------------------

    def consume(self, battle: NormalizedBattleAggregate) -> None:
        """
        Consume una battle normalizada y la agrega a su duelo correspondiente.

        Parámetros:
            battle: instancia de NormalizedBattleAggregate.

        No realiza validaciones de dominio adicionales.
        Solo agrupa por clave lógica.
        """

        key = DuelKey(
            season_name=battle.event.season_name,
            event_name=battle.event.event_name,
            duel_sequence_number=battle.duel.normal_duel_sequence_number,
        )

        # Agrupación incremental por clave
        self._duels.setdefault(key, []).append(battle)

    # ---------------------------------------------------------

    def finalize(self) -> Tuple[NormalizedDuelAggregate, ...]:
        """
        Finaliza la agregación y construye los duelos completos.

        Reglas de dominio aplicadas:
            - Las battles empatadas no suman wins.
            - Debe existir al menos una battle decisiva.
            - Solo puede existir un jugador con mayor cantidad de wins.
            - No se permiten empates en el duelo.

        Retorna:
            Tupla inmutable de NormalizedDuelAggregate.
        """

        duel_aggregates: List[NormalizedDuelAggregate] = []

        for key, battles in self._duels.items():

            # Orden explícito por secuencia de battle
            battles_sorted = sorted(
                battles,
                key=lambda b: b.battle.battle_sequence_number
            )

            # Conteo de victorias por jugador
            wins_by_player = defaultdict(int)

            # Conjunto total de jugadores que participaron en el duelo
            players_in_duel = set()

            for battle in battles_sorted:

                # Registrar todos los participantes
                for p in battle.participants:
                    players_in_duel.add(p.player_name)

                # Las battles empatadas no cuentan para el resultado del duelo
                if battle.battle.is_draw:
                    continue

                winner_position = battle.battle.winner_position

                # Seguridad adicional: si no hay posición ganadora válida
                if winner_position is None:
                    continue

                winner_name = battle.participants[winner_position - 1].player_name
                wins_by_player[winner_name] += 1

            # Debe existir al menos una battle decisiva
            if not wins_by_player:
                raise ValueError(
                    f"Duel {key} has no decisive battles."
                )

            # Determinar jugador con mayor número de wins
            sorted_wins = sorted(
                wins_by_player.items(),
                key=lambda item: item[1],
                reverse=True
            )

            top_player, top_wins = sorted_wins[0]

            # Verificar que no exista empate en número de wins
            tied_players = [
                player for player, wins in wins_by_player.items()
                if wins == top_wins
            ]

            if len(tied_players) > 1:
                raise ValueError(
                    f"Duel {key} has tied winners: {tied_players}"
                )

            # Todos los demás jugadores son perdedores
            losers = tuple(
                player for player in players_in_duel
                if player != top_player
            )

            winner_team_name = None
            loser_team_names = tuple()

            if battles_sorted[0].duel.is_team_duel:

                team_by_player = {}

                for battle in battles_sorted:
                    for p in battle.participants:
                        team_by_player[p.player_name] = p.team_name

                winner_team_name = team_by_player[top_player]

                loser_team_names = tuple({
                    team_by_player[p]
                    for p in players_in_duel
                    if p != top_player
                })

            duel_aggregates.append(
                NormalizedDuelAggregate(
                    event=battles_sorted[0].event,
                    duel=battles_sorted[0].duel,
                    battles=tuple(battles_sorted),
                    winner_player_name=top_player,
                    loser_player_names=losers,
                    winner_team_name=winner_team_name,
                    loser_team_names=loser_team_names
                )
            )

        # Proyección final inmutable
        return tuple(duel_aggregates)
