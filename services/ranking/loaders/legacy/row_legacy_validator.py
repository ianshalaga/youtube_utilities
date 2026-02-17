from typing import Tuple, Set

from domain.ranking.scoring.scoring_v1 import RoundScoringV1
from services.ranking.loaders.legacy.row_legacy_dto import RowLegacyDTO

_VALID_CHARACTERS = (
    "2B",
    "Amy",
    "Astaroth",
    "Azwel",
    "Cassandra",
    "Cervantes",
    "Geralt",
    "Groh",
    "Haohmaru",
    "Hilde",
    "Hwang",
    "Ivy",
    "Kilik",
    "Maxi",
    "Mitsurugi",
    "Nightmare",
    "Raphael",
    "Seong Mi-na",
    "Setsuka",
    "Siegfried",
    "Sophitia",
    "Taki",
    "Talim",
    "Tira",
    "Voldo",
    "Xianghua",
    "Yoshimitsu",
    "Zasalamel",
)

_VALID_COUNTRIES = (
    "Argentina",
    "Brasil",
    "Chile",
    "Paraguay",
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


class RowLegacyValidator:
    """
    Validador semántico de filas legacy.

    Responsabilidad:
    - Validar invariantes de dominio.
    - No transforma datos.
    - No accede a la base de datos.
    - No crea entidades ORM.
    - No modifica el DTO.

    Lanza ValueError si alguna regla de dominio es violada.
    """

    # ===============================
    # Public API
    # ===============================

    @classmethod
    def validate(cls, dto: RowLegacyDTO) -> None:
        cls._validate_game_context(dto)
        cls._validate_event_context(dto)
        cls._validate_duel_context(dto)
        cls._validate_battle_context(dto)
        cls._validate_team_context(dto)
        cls._validate_round_context(dto)

    @staticmethod
    def _validate_game_context(dto: RowLegacyDTO) -> None:
        if dto.game_name != "Soulcalibur VI":
            raise ValueError("Only Soulcalibur VI is supported.")

        if dto.game_version != "2.31":
            raise ValueError("Only Soulcalibur VI 2.31 is supported.")

        if dto.event_platform not in ("PC", "PS4"):
            raise ValueError("Only PC and PS4 platforms are supported.")

        if dto.region_name != "SAS":
            raise ValueError("Only SAS region is supported.")

    @staticmethod
    def _validate_event_context(dto: RowLegacyDTO) -> None:
        if dto.season_name not in ("S1", "S2"):
            raise ValueError("Only S1 and S2 seasons are supported.")

        if not dto.event_name.startswith("SSL"):
            raise ValueError("Only SSL events are supported.")

        if dto.event_brackets:
            if not dto.event_brackets.startswith("https://"):
                raise ValueError(
                    "event_brackets must be a valid URL."
                )

        if dto.event_playlist:
            if not dto.event_playlist.startswith("https://"):
                raise ValueError(
                    "event_playlist must be a valid URL."
                )

    @staticmethod
    def _validate_duel_context(dto: RowLegacyDTO) -> None:
        if dto.normal_duel_order <= 0:
            raise ValueError("normal_duel_order must be positive.")

        if dto.combat_order <= 0:
            raise ValueError("combat_order must be positive.")

        if dto.duel_video:
            if not dto.duel_video.startswith("https://"):
                raise ValueError(
                    "duel_video must be a valid URL."
                )

        # Duel type must exist
        # if not dto.normal_duel_type:
        #     raise ValueError("normal_duel_type is required.")

        # Team duel consistency
        # is_team_duel = dto.player_1_team is not None

        # if is_team_duel:
        #     if dto.team_duel_order is None:
        #         raise ValueError("team_duel_order required for team duel.")

        #     if dto.team_duel_type is None:
        #         raise ValueError("team_duel_type required for team duel.")
        # else:
        #     if dto.team_duel_order is not None:
        #         raise ValueError(
        #             "team_duel_order must be None for non-team duel.")

        #     if dto.team_duel_type is not None:
        #         raise ValueError(
        #             "team_duel_type must be None for non-team duel.")

    @staticmethod
    def _validate_battle_context(dto: RowLegacyDTO) -> None:
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

    @staticmethod
    def _validate_team_context(dto: RowLegacyDTO) -> None:
        if dto.player_1_team and dto.player_2_team:
            if dto.player_1_team == dto.player_2_team:
                raise ValueError(
                    "A team cannot fight against itself.")

        if dto.team_duel_order is not None and dto.team_duel_order <= 0:
            raise ValueError("team_duel_order must be positive.")

    @staticmethod
    def _validate_round_context(dto: RowLegacyDTO) -> None:
        round_scoring = RoundScoringV1()
        valid_results = round_scoring.valid_codes()

        for idx, (r1, r2) in enumerate(zip(dto.rounds_p1, dto.rounds_p2), start=1):
            # Round result validation
            if r1 not in valid_results:
                raise ValueError(
                    f"Invalid round result for p1 in round {idx}: {r1}")

            if r2 not in valid_results:
                raise ValueError(
                    f"Invalid round result for p2 in round {idx}: {r2}")

            # Win/loss consistency validation
            if round_scoring.is_win(r1) and not round_scoring.is_loss(r2):
                raise ValueError(
                    f"Round {idx} no respects win/loss rule for player 2 on: {r2}.")

            if round_scoring.is_loss(r1) and not round_scoring.is_win(r2):
                raise ValueError(
                    f"Round {idx} no respects win/loss rule for player 2 on: {r2}.")

            # Perfect win/loss consistency validation
            if round_scoring.is_perfect_win(r1) and not round_scoring.is_perfect_loss(r2):
                raise ValueError(
                    f"Round {idx} no respects perfect win/perfect loss rule for player 2 on: {r2}."
                )

            if round_scoring.is_perfect_loss(r1) and not round_scoring.is_perfect_win(r2):
                raise ValueError(
                    f"Round {idx} no respects perfect win/perfect loss rule for player 2 on: {r2}."
                )

            # Draw consistency validation
            if round_scoring.is_draw(r1) and not round_scoring.is_draw(r2):
                raise ValueError(
                    f"Round {idx} no respects draw rule for player 2 on: {r2}."
                )

            if round_scoring.is_draw(r2) and not round_scoring.is_draw(r1):
                raise ValueError(
                    f"Round {idx} no respects draw rule for player 1 on: {r1}."
                )

        p1_wins = sum(
            1 for r1 in dto.rounds_p1 if round_scoring.is_win_result(r1))
        p2_wins = sum(
            1 for r2 in dto.rounds_p2 if round_scoring.is_win_result(r2))
        p1_losses = sum(
            1 for r1 in dto.rounds_p1 if round_scoring.is_loss_result(r1))
        p2_losses = sum(
            1 for r2 in dto.rounds_p2 if round_scoring.is_loss_result(r2))

        if p1_wins < p2_losses:
            raise ValueError(
                f"Player 1 wins {p1_wins} but player 2 losses {p2_losses}.")

        if p2_wins < p1_losses:
            raise ValueError(
                f"Player 2 wins {p2_wins} but player 1 losses {p1_losses}.")
