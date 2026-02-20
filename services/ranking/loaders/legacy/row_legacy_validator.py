"""
Row Legacy Validator
====================

Notas de implementación
-----------------------

Este módulo forma parte del pipeline de carga legacy:

    CSV → Mapper → DTO → Validator → Normalizer → Aggregator → Loader

Responsabilidad del Validator:

- Validar invariantes semánticas de dominio.
- Garantizar coherencia estructural avanzada.
- No transformar datos.
- No acceder a la base de datos.
- No crear entidades ORM.
- No modificar el DTO.
- No realizar agregación.

Este componente asume que:
- La estructura sintáctica ya fue validada por el Mapper.
- La coherencia estructural básica fue validada por el DTO.

El Validator valida reglas de dominio específicas del sistema legacy.
Lanza ValueError si alguna regla es violada.
"""

from domain.ranking.scoring.scoring_v1 import RoundScoringV1
from services.ranking.loaders.legacy.row_legacy_dto import RowLegacyDTO


"""
Descripción general
-------------------

Este módulo define:

1. Conjuntos cerrados (_VALID_*) que representan dominio permitido
   para el entorno legacy (hardcoded intencionalmente).

2. RowLegacyValidator:
   Clase estática que valida:

   - Contexto del juego
   - Contexto del evento
   - Contexto del duelo
   - Contexto de batalla
   - Contexto de equipos
   - Coherencia de rounds

El diseño es completamente determinista y sin efectos secundarios.
"""


# =========================
# Dominio permitido (Legacy)
# =========================

_VALID_CHARACTERS = (
    "2B", "Amy", "Astaroth", "Azwel", "Cassandra", "Cervantes",
    "Geralt", "Groh", "Haohmaru", "Hilde", "Hwang", "Ivy",
    "Kilik", "Maxi", "Mitsurugi", "Nightmare", "Raphael",
    "Seong Mi-na", "Setsuka", "Siegfried", "Sophitia", "Taki",
    "Talim", "Tira", "Voldo", "Xianghua", "Yoshimitsu", "Zasalamel",
)

_VALID_COUNTRIES = (
    "Argentina", "Brasil", "Chile", "Paraguay",
)

_VALID_STAGES = (
    "Astral Chaos: Tide of the Damned",
    "City Ruins: Eternal Apocalypse",
    "Cursed Moonlit Woods",
    "Gairyu Isle",
    "Indian Port: Impending Storm",
    "Kunpaetku Temple: Serpentine Banquet",
    "Master Swordman's Cave: Azure Horizon",
    "Master Swordman's Cave: Wicked Depths",
    "Motien Pass Ruins",
    "Murakumo Shrine Grounds",
    "Ostrheinsburg Castle: Hall of the Chosen",
    "Replica Kaer Morhen",
    "Shrine of Eurydice: Cloud Sanctuary",
    "Silver Wolves' Haven",
    "Snow-capped Showdown",
    "Sunken Desert Ruins",
    "Windswept Plains",
)


# =========================
# Validator
# =========================


class RowLegacyValidator:
    """
    Validador semántico de filas legacy.

    Opera sobre un RowLegacyDTO previamente construido y validado
    estructuralmente.

    Responsabilidades:
    - Validar invariantes del dominio.
    - Validar coherencia entre campos.
    - Validar reglas de scoring de rounds.

    No:
    - Modifica el DTO.
    - Realiza persistencia.
    - Crea modelos ORM.
    - Deriva aggregates.
    """

    # ===============================
    # Public API
    # ===============================

    @classmethod
    def validate(cls, dto: RowLegacyDTO) -> None:
        """
        Punto de entrada principal.

        Ejecuta todas las validaciones de dominio
        en orden determinista.
        """
        cls._validate_game_context(dto)
        cls._validate_event_context(dto)
        cls._validate_duel_context(dto)
        cls._validate_battle_context(dto)
        cls._validate_team_context(dto)
        cls._validate_round_context(dto)

    # ===============================
    # Context Validators
    # ===============================

    @staticmethod
    def _validate_game_context(dto: RowLegacyDTO) -> None:
        """
        Valida restricciones rígidas del entorno legacy.

        El sistema legacy solo soporta:
        - Soulcalibur VI
        - Versión 2.31
        - Plataformas PC o PS4
        - Región SAS
        """

        if dto.game_name != "Soulcalibur VI":
            raise ValueError("Only Soulcalibur VI is supported.")

        if dto.game_version != "2.31":
            raise ValueError("Only Soulcalibur VI 2.31 is supported.")

        if dto.event_platform not in ("PC", "PS4"):
            raise ValueError("Only PC and PS4 platforms are supported.")

        if dto.region_name != "SAS":
            raise ValueError("Only SAS region is supported.")

    # ---------------------------------------------------------

    @staticmethod
    def _validate_event_context(dto: RowLegacyDTO) -> None:
        """
        Valida coherencia del contexto de evento.

        - Solo temporadas S1 y S2.
        - Solo eventos con prefijo SSL.
        - URLs deben comenzar con https:// si existen.
        """

        if dto.season_name not in ("S1", "S2"):
            raise ValueError("Only S1 and S2 seasons are supported.")

        if not dto.event_name.startswith("SSL"):
            raise ValueError("Only SSL events are supported.")

        if dto.event_brackets and not dto.event_brackets.startswith("https://"):
            raise ValueError("event_brackets must be a valid URL.")

        if dto.event_playlist and not dto.event_playlist.startswith("https://"):
            raise ValueError("event_playlist must be a valid URL.")

    # ---------------------------------------------------------

    @staticmethod
    def _validate_duel_context(dto: RowLegacyDTO) -> None:
        """
        Valida contexto estructural del duelo.

        - Órdenes deben ser positivos.
        - URLs deben ser válidas si existen.
        """

        if dto.normal_duel_order <= 0:
            raise ValueError("normal_duel_order must be positive.")

        if dto.combat_order <= 0:
            raise ValueError("combat_order must be positive.")

        if dto.duel_video and not dto.duel_video.startswith("https://"):
            raise ValueError("duel_video must be a valid URL.")

        # Validaciones de team duel están deliberadamente comentadas
        # ya que este módulo solo soporta ejecución legacy única
        # y la consistencia estructural ya fue verificada en el DTO.

    # ---------------------------------------------------------

    @staticmethod
    def _validate_battle_context(dto: RowLegacyDTO) -> None:
        """
        Valida coherencia de batalla.

        - Un jugador no puede enfrentarse a sí mismo.
        - Personajes deben pertenecer al dominio permitido.
        - Países deben pertenecer al dominio permitido.
        - Stage debe pertenecer al dominio permitido.
        """

        if dto.player_1_name == dto.player_2_name:
            raise ValueError("A player cannot fight against himself.")

        if dto.character_1_name not in _VALID_CHARACTERS:
            raise ValueError(f"Invalid character name: {dto.character_1_name}")

        if dto.character_2_name not in _VALID_CHARACTERS:
            raise ValueError(f"Invalid character name: {dto.character_2_name}")

        if dto.player_1_country not in _VALID_COUNTRIES:
            raise ValueError(f"Invalid country name: {dto.player_1_country}")

        if dto.player_2_country not in _VALID_COUNTRIES:
            raise ValueError(f"Invalid country name: {dto.player_2_country}")

        if dto.stage_name not in _VALID_STAGES:
            raise ValueError(f"Invalid stage name: {dto.stage_name}")

    # ---------------------------------------------------------

    @staticmethod
    def _validate_team_context(dto: RowLegacyDTO) -> None:
        """
        Valida coherencia mínima de contexto de equipos.

        - Un equipo no puede enfrentarse a sí mismo.
        - team_duel_order debe ser positivo si existe.
        """

        if dto.player_1_team and dto.player_2_team:
            if dto.player_1_team == dto.player_2_team:
                raise ValueError("A team cannot fight against itself.")

        if dto.team_duel_order is not None and dto.team_duel_order <= 0:
            raise ValueError("team_duel_order must be positive.")

    # ---------------------------------------------------------

    @staticmethod
    def _validate_round_context(dto: RowLegacyDTO) -> None:
        """
        Valida coherencia semántica de rounds.

        - Cada código debe pertenecer a RoundScoringV1.valid_codes().
        - Win/Loss deben ser consistentes entre jugadores.
        - Perfect win/loss deben corresponder.
        - Draw debe ser simétrico.
        - Conteo total de wins y losses debe ser coherente.
        """

        round_scoring = RoundScoringV1()
        valid_results = round_scoring.valid_codes()

        # Validación round por round
        for idx, (r1, r2) in enumerate(zip(dto.rounds_p1, dto.rounds_p2), start=1):

            if r1 not in valid_results:
                raise ValueError(
                    f"Invalid round result for p1 in round {idx}: {r1}"
                )

            if r2 not in valid_results:
                raise ValueError(
                    f"Invalid round result for p2 in round {idx}: {r2}"
                )

            # Win/Loss simétrico
            if round_scoring.is_win(r1) and not round_scoring.is_loss(r2):
                raise ValueError(
                    f"Round {idx} violates win/loss rule for player 2: {r2}."
                )

            if round_scoring.is_loss(r1) and not round_scoring.is_win(r2):
                raise ValueError(
                    f"Round {idx} violates win/loss rule for player 2: {r2}."
                )

            # Perfect win/loss simétrico
            if round_scoring.is_perfect_win(r1) and not round_scoring.is_perfect_loss(r2):
                raise ValueError(
                    f"Round {idx} violates perfect win/loss rule for player 2: {r2}."
                )

            if round_scoring.is_perfect_loss(r1) and not round_scoring.is_perfect_win(r2):
                raise ValueError(
                    f"Round {idx} violates perfect win/loss rule for player 2: {r2}."
                )

            # Draw simétrico
            if round_scoring.is_draw(r1) and not round_scoring.is_draw(r2):
                raise ValueError(
                    f"Round {idx} violates draw rule for player 2: {r2}."
                )

            if round_scoring.is_draw(r2) and not round_scoring.is_draw(r1):
                raise ValueError(
                    f"Round {idx} violates draw rule for player 1: {r1}."
                )

        # Validación agregada de coherencia de conteos
        p1_wins = sum(
            1 for r in dto.rounds_p1 if round_scoring.is_win_result(r))
        p2_wins = sum(
            1 for r in dto.rounds_p2 if round_scoring.is_win_result(r))
        p1_losses = sum(
            1 for r in dto.rounds_p1 if round_scoring.is_loss_result(r))
        p2_losses = sum(
            1 for r in dto.rounds_p2 if round_scoring.is_loss_result(r))

        # Wins de un jugador deben reflejar losses del otro
        if p1_wins < p2_losses:
            raise ValueError(
                f"Player 1 wins {p1_wins} but player 2 losses {p2_losses}."
            )

        if p2_wins < p1_losses:
            raise ValueError(
                f"Player 2 wins {p2_wins} but player 1 losses {p1_losses}."
            )
