from services.ranking.loaders.legacy.row_legacy_dto import LegacyRowDTO

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
    def validate(cls, dto: LegacyRowDTO) -> None:
        cls._validate_game_context(dto)
        cls._validate_event_context(dto)
        cls._validate_duel_context(dto)
        cls._validate_battle_context(dto)
        cls._validate_team_context(dto)

        cls._validate_team_rules(dto)
        cls._validate_context_rules(dto)

    @staticmethod
    def _validate_game_context(dto: LegacyRowDTO) -> None:
        if dto.game_name != "Soulcalibur VI":
            raise ValueError("Only Soulcalibur VI is supported.")

        if dto.game_version != "2.31":
            raise ValueError("Only Soulcalibur VI 2.31 is supported.")

        if dto.event_platform not in ("PC", "PS4"):
            raise ValueError("Only PC and PS4 platforms are supported.")

        if dto.region_name != "SAS":
            raise ValueError("Only SAS region is supported.")

    @staticmethod
    def _validate_event_context(dto: LegacyRowDTO) -> None:
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
    def _validate_duel_context(dto: LegacyRowDTO) -> None:
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
    def _validate_battle_context(dto: LegacyRowDTO) -> None:
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
    def _validate_team_context(dto: LegacyRowDTO) -> None:
        team_fields = (
            dto.player_1_team,
            dto.player_2_team,
            dto.team_duel_order,
            dto.team_duel_type,
        )

        all_none = all(field is None for field in team_fields)
        all_not_none = all(field is not None for field in team_fields)

        if not (all_none or all_not_none):
            raise ValueError(
                "All team fields must be set together or not at all.")

        if dto.player_1_team and dto.player_2_team:
            if dto.player_1_team == dto.player_2_team:
                raise ValueError(
                    "A team cannot fight against itself.")

        if dto.team_duel_order and dto.team_duel_order <= 0:
            raise ValueError("team_duel_order must be positive.")

    # @@@@

    @staticmethod
    def _validate_round_context(dto: LegacyRowDTO) -> None:
        allowed_results = {"W", "L", "D"}  # Adjust to real domain values

        for idx, (r1, r2) in enumerate(zip(dto.rounds_p1, dto.rounds_p2), start=1):
            if r1 not in allowed_results:
                raise ValueError(
                    f"Invalid round result for p1 in round {idx}: {r1}")

            if r2 not in allowed_results:
                raise ValueError(
                    f"Invalid round result for p2 in round {idx}: {r2}")

            # Basic symmetry rule
            if r1 == "W" and r2 != "L":
                raise ValueError(f"Inconsistent round {idx}: W must match L.")

            if r1 == "L" and r2 != "W":
                raise ValueError(f"Inconsistent round {idx}: L must match W.")

            if r1 == "D" and r2 != "D":
                raise ValueError(f"Inconsistent round {idx}: draw mismatch.")

        RowLegacyValidator._validate_round_win_consistency(dto)

    @staticmethod
    def _validate_round_win_consistency(dto: LegacyRowDTO) -> None:
        wins_p1 = dto.rounds_p1.count("W")
        wins_p2 = dto.rounds_p2.count("W")

        if wins_p1 == wins_p2:
            # Could be draw depending on rules
            pass

        # Optional domain rule example:
        # if wins_p1 > 3 or wins_p2 > 3:
        #     raise ValueError("Too many wins for legacy duel format.")

    # ===============================
    # Team Rules
    # ===============================

    @staticmethod
    def _validate_team_rules(dto: LegacyRowDTO) -> None:
        if dto.player_1_team and dto.player_2_team:
            if dto.player_1_team == dto.player_2_team:
                raise ValueError(
                    "Both players cannot belong to the same team.")

    # ===============================
    # Context Rules
    # ===============================

    @staticmethod
    def _validate_context_rules(dto: LegacyRowDTO) -> None:
        # if not dto.game_name:
        #     raise ValueError("game_name is required.")

        # if not dto.event_name:
        #     raise ValueError("event_name is required.")

        # if not dto.stage_name:
        #     raise ValueError("stage_name is required.")

        # Future extension:
        # Validate region format
        # Validate platform format
        # Validate season naming conventions
        ...
