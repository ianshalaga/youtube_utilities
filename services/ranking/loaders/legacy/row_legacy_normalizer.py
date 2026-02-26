"""
Row Legacy Normalizer
=====================

Notas de implementación
-----------------------

Este módulo forma parte del pipeline de carga legacy:

    CSV → Mapper → DTO → Validator → Normalizer → Aggregator → Loader

Responsabilidad del Normalizer:

- Transformar un RowLegacyDTO válido en un NormalizedBattleAggregate.
- Derivar información intra-fila (ej. ganador de la batalla).
- No acceder a base de datos.
- No validar reglas de dominio (eso corresponde al Validator).
- No persistir entidades (eso corresponde al Loader).
- No replicar el modelo ORM.

El resultado es un modelo intermedio semántico, independiente de la
infraestructura de persistencia.

Todas las funciones auxiliares son puras, deterministas y sin efectos secundarios.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional, Tuple

from domain.ranking.scoring.scoring_v1 import RoundScoringV1
from services.ranking.loaders.legacy.row_legacy_dto import RowLegacyDTO


"""
Descripción general
-------------------

Este documento define:

1. Estructuras Normalized*Context que representan una unidad semántica
   coherente de importación (Aggregate).
2. BattleResult como objeto intermedio para encapsular el resultado
   derivado de una batalla.
3. RowLegacyNormalizer, encargado de transformar un DTO validado en
   un NormalizedBattleAggregate listo para ser consumido por un
   Aggregator o Loader.

El diseño evita acoplamiento con el modelo relacional (ORM).
"""


# =========================
# Aggregate Models
# =========================


@dataclass(frozen=True)
class NormalizedEventContext:
    """
    Representa el contexto del evento necesario para persistencia.

    Contiene información suficiente para que el Loader resuelva:
    - Game
    - Franchise
    - GameVersion
    - Platform
    - Season
    - Region
    - EventType
    - Event
    """
    game_name: str
    game_franchise_name: str  # derivado del nombre del juego
    game_version: str
    platform_name: str
    region_name: str
    season_name: str
    event_type_name: str  # derivado del nombre del evento
    event_name: str
    event_date: date
    brackets_url: Optional[str]
    playlist_url: Optional[str]


@dataclass(frozen=True)
class NormalizedDuelContext:
    """
    Representa el contexto lógico del duelo.
    No replica tablas ORM; modela el duelo como unidad semántica.
    """
    normal_duel_sequence_number: int
    normal_duel_type_name: str
    duel_video_url: Optional[str]
    is_team_duel: bool  # derivado
    team_duel_sequence_number: Optional[int]
    team_duel_type_name: Optional[str]


@dataclass(frozen=True)
class NormalizedBattleContext:
    """
    Representa la información estructural y derivada de una batalla.
    """
    battle_sequence_number: int
    stage_name: str
    is_draw: bool  # derivado
    winner_position: Optional[int]  # derivado
    loser_position: Optional[int]  # derivado
    winner_player_name: Optional[str]  # derivado
    loser_player_name: Optional[str]  # derivado


@dataclass(frozen=True)
class BattleResult:
    """
    Objeto auxiliar que encapsula el resultado derivado de una batalla.
    """
    is_draw: bool
    winner_position: Optional[int]
    loser_position: Optional[int]


@dataclass(frozen=True)
class NormalizedRoundContext:
    """
    Representa un round individual dentro de la batalla.
    No deriva ganador ya que puede inferirse vía RoundScoring.
    """
    round_sequence_number: int
    p1_result_code: str
    p2_result_code: str
    is_draw: bool
    winner_position: Optional[int]
    loser_position: Optional[int]


@dataclass(frozen=True)
class NormalizedParticipant:
    """
    Representa un participante en la batalla.
    """
    player_name: str
    character_name: str
    country: str
    team_name: Optional[str]


@dataclass(frozen=True)
class NormalizedBattleAggregate:
    """
    Unidad semántica completa de importación.

    Representa:
    Event → Duel → Battle → Participants → Rounds

    Es la estructura que será consumida por el Aggregator
    o directamente por el Loader.
    """
    event: NormalizedEventContext
    duel: NormalizedDuelContext
    battle: NormalizedBattleContext
    participants: Tuple[NormalizedParticipant, NormalizedParticipant]
    rounds: Tuple[NormalizedRoundContext, ...]


# =========================
# Normalizer
# =========================


class RowLegacyNormalizer:
    """
    Orquestador de normalización intra-fila.

    Toma un DTO validado y construye un NormalizedBattleAggregate.
    """

    @staticmethod
    def normalize(dto: RowLegacyDTO) -> NormalizedBattleAggregate:
        """
        Normaliza una fila legacy en un Aggregate semántico.

        No valida dominio.
        No persiste.
        No accede a infraestructura.
        """

        # --- Build event context ---
        event = NormalizedEventContext(
            game_name=dto.game_name,
            game_franchise_name=RowLegacyNormalizer._get_franchise_name(
                dto.game_name
            ),
            game_version=dto.game_version,
            platform_name=dto.event_platform,
            region_name=dto.region_name,
            season_name=dto.season_name,
            event_type_name=RowLegacyNormalizer._get_event_type_name(
                dto.event_name
            ),
            event_name=dto.event_name,
            event_date=dto.event_date,
            brackets_url=dto.brackets_url,
            playlist_url=dto.playlist_url,
        )

        # --- Build duel context ---
        duel = NormalizedDuelContext(
            normal_duel_sequence_number=dto.normal_duel_order,
            normal_duel_type_name=dto.normal_duel_type,
            duel_video_url=dto.duel_video,
            is_team_duel=RowLegacyNormalizer._get_is_team_duel(
                event.event_type_name,
                dto.player_1_team,
            ),
            team_duel_sequence_number=dto.team_duel_order,
            team_duel_type_name=dto.team_duel_type,
        )

        # --- Derive battle result ---
        round_scoring = RoundScoringV1()
        battle_result = RowLegacyNormalizer._get_battle_result(
            dto.rounds_p1,
            dto.rounds_p2,
            round_scoring,
        )

        if battle_result.is_draw:
            winner_name = None
            loser_name = None
        else:
            winner_name = (
                dto.player_1_name
                if battle_result.winner_position == 1
                else dto.player_2_name
            )
            loser_name = (
                dto.player_2_name
                if battle_result.winner_position == 1
                else dto.player_1_name
            )

        # --- Build battle context ---
        battle = NormalizedBattleContext(
            battle_sequence_number=dto.combat_order,
            stage_name=dto.stage_name,
            is_draw=battle_result.is_draw,
            winner_position=battle_result.winner_position,
            loser_position=battle_result.loser_position,
            winner_player_name=winner_name,
            loser_player_name=loser_name
        )

        # --- Build round contexts ---
        rounds = []

        for i, (r1, r2) in enumerate(zip(dto.rounds_p1, dto.rounds_p2), start=1):

            p1_win = round_scoring.is_win_result(r1)
            p2_win = round_scoring.is_win_result(r2)

            if p1_win and not p2_win:
                is_draw = False
                winner_position = 1
                loser_position = 2
            elif p2_win and not p1_win:
                is_draw = False
                winner_position = 2
                loser_position = 1
            else:
                is_draw = True
                winner_position = None
                loser_position = None

            rounds.append(
                NormalizedRoundContext(
                    round_sequence_number=i,
                    p1_result_code=r1,
                    p2_result_code=r2,
                    is_draw=is_draw,
                    winner_position=winner_position,
                    loser_position=loser_position,
                )
            )

        rounds = tuple(rounds)

        # --- Build participants ---
        p1 = NormalizedParticipant(
            player_name=dto.player_1_name,
            character_name=dto.character_1_name,
            country=dto.player_1_country,
            team_name=dto.player_1_team,
        )

        p2 = NormalizedParticipant(
            player_name=dto.player_2_name,
            character_name=dto.character_2_name,
            country=dto.player_2_country,
            team_name=dto.player_2_team,
        )

        return NormalizedBattleAggregate(
            event=event,
            duel=duel,
            battle=battle,
            participants=(p1, p2),
            rounds=rounds,
        )

    # ---------------------------------------------------------

    @staticmethod
    def _get_franchise_name(game_name: str) -> str:
        """
        Deriva el nombre de la franquicia a partir del nombre del juego.
        Ejemplo: 'Soulcalibur VI' → 'Soulcalibur'
        """
        return game_name.split()[0]

    @staticmethod
    def _get_event_type_name(event_name: str) -> str:
        """
        Determina el tipo de evento a partir del prefijo del nombre.
        """
        _EVENT_TYPE_PREFIX_MAP = {
            "SSLTSE": "tournament_special",
            "SSLTT": "team_tournament",
            "SSLT": "tournament",
            "SSLL": "league",
        }

        prefix = event_name.split()[0]

        try:
            return _EVENT_TYPE_PREFIX_MAP[prefix]
        except KeyError:
            raise ValueError(f"Unknown event type prefix: {prefix}")

    @staticmethod
    def _get_is_team_duel(
        event_type_name: str,
        player_1_team: Optional[str],
    ) -> bool:
        """
        Determina si el duelo es por equipos.

        Requiere:
        - Que el tipo de evento sea 'team_tournament'
        - Que exista información de equipo en el DTO
        """
        return (
            event_type_name == "team_tournament"
            and player_1_team is not None
        )

    @staticmethod
    def _get_battle_result(
        rounds_p1: Tuple[str, ...],
        rounds_p2: Tuple[str, ...],
        round_scoring: RoundScoringV1,
    ) -> BattleResult:
        """
        Deriva el resultado de la batalla a partir de los códigos de round.
        """

        p1_wins = sum(
            1 for r in rounds_p1 if round_scoring.is_win_result(r)
        )
        p2_wins = sum(
            1 for r in rounds_p2 if round_scoring.is_win_result(r)
        )

        if p1_wins == p2_wins:
            return BattleResult(True, None, None)
        elif p1_wins > p2_wins:
            return BattleResult(False, 1, 2)
        else:
            return BattleResult(False, 2, 1)
