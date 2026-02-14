class RowLegacyMapper:
    """
    Mapeador de filas CSV legacy.
    Adaptador de estructura cruda.
    Validador sintáctico.

    Responsabilidad:
    - Resolver nombres de columnas.
    - Normalizar strings (strip).
    - Encapsular acceso a dict[str,str].
    - NO accede a DB
    - No tiene tipos fuertes.
    - No infiere (parsea) dominio.
    - No transforma a tipos Python reales.

    Es un wrapper elegante sobre el CSV.

    Solo valida estructura sintáctica (no dominio):
    - Empty row.
    - Missing headers.
    - Unexpected headers.
    - Player range.
    - Round range.
    """

    _FIELDS_MAP = {
        # El csv legacy contiene 34 campos
        # Context
        "game_name": "game",
        "game_version": "version",
        "event_platform": "platform",
        "region_name": "region",
        # Season / Event
        "season_name": "season",
        "event_name": "event",
        "event_date": "date",
        "event_brackets": "brackets",
        "event_playlist": "playlist",
        # Duel
        "duel_order": "duel",
        "individual_duel_type": "duel_type",
        "duel_video": "video",
        "combat_order": "combat",
        # Battle
        "player_1_name": "player1",
        "player_2_name": "player2",
        "character_1_name": "character1",
        "character_2_name": "character2",
        "player_1_country": "p1_country",
        "player_2_country": "p2_country",
        "stage_name": "stage",
        # Team
        "player_1_team": "p1_team",
        "player_2_team": "p2_team",
        "team_duel_order": "team_duel",
        "team_duel_type": "t_duel_type",
        # Round
        "round_1_p1": "r1_p1",
        "round_2_p1": "r2_p1",
        "round_3_p1": "r3_p1",
        "round_4_p1": "r4_p1",
        "round_5_p1": "r5_p1",
        "round_1_p2": "r1_p2",
        "round_2_p2": "r2_p2",
        "round_3_p2": "r3_p2",
        "round_4_p2": "r4_p2",
        "round_5_p2": "r5_p2",
    }

    def __init__(self, row: dict[str, str]):
        self._row = row
        self._validate_row_headers()

    def _get(self, logical_name: str):
        header = self._FIELDS_MAP[logical_name]
        value = self._row.get(header)
        return value.strip() if value else None

    def _validate_row_headers(self):
        if not self._row:
            raise ValueError("Empty CSV row.")

        expected = set(self._FIELDS_MAP.values())
        present = set(self._row.keys())
        missing = expected - present
        unexpected = present - expected

        if missing:
            raise ValueError(f"Missing required headers: {sorted(missing)}")

        if unexpected:
            raise ValueError(f"Unexpected headers: {sorted(unexpected)}")

    # --- Context ---
    @property
    def game_name(self):
        return self._get("game_name")

    @property
    def game_version(self):
        return self._get("game_version")

    @property
    def event_platform(self):
        return self._get("event_platform")

    @property
    def region_name(self):
        return self._get("region_name")

    # --- Season / Event ---
    @property
    def season_name(self):
        return self._get("season_name")

    @property
    def event_name(self):
        return self._get("event_name")

    @property
    def event_date(self):
        return self._get("event_date")

    @property
    def event_brackets(self):
        return self._get("event_brackets")

    @property
    def event_playlist(self):
        return self._get("event_playlist")

    # --- Duel ---
    @property
    def duel_order(self):
        return self._get("duel_order")

    @property
    def individual_duel_type(self):
        return self._get("individual_duel_type")

    @property
    def duel_video(self):
        return self._get("duel_video")

    @property
    def combat_order(self):
        return self._get("combat_order")

    # --- Battle ---
    @property
    def player_1_name(self):
        return self._get("player_1_name")

    @property
    def player_2_name(self):
        return self._get("player_2_name")

    @property
    def character_1_name(self):
        return self._get("character_1_name")

    @property
    def character_2_name(self):
        return self._get("character_2_name")

    @property
    def player_1_country(self):
        return self._get("player_1_country")

    @property
    def player_2_country(self):
        return self._get("player_2_country")

    @property
    def stage_name(self):
        return self._get("stage_name")

    # --- Team ---
    @property
    def player_1_team(self):
        return self._get("player_1_team")

    @property
    def player_2_team(self):
        return self._get("player_2_team")

    @property
    def team_duel_order(self):
        return self._get("team_duel_order")

    @property
    def team_duel_type(self):
        return self._get("team_duel_type")

    # --- Round ---
    def round_result(self, round_number: int, player: int) -> str | None:
        """
        Devuelve el resultado de un round para un jugador.

        player: 1 o 2
        round_number: 1..5
        """
        if player not in (1, 2):
            raise ValueError(f"Invalid player index: {player}")

        if round_number not in (1, 2, 3, 4, 5):
            raise ValueError(f"Invalid round number: {round_number}")

        key = f"round_{round_number}_p{player}"
        return self._get(key)

    @classmethod
    def _validate_field_map_definition(cls):
        physical_names = list(cls._FIELDS_MAP.values())

        if len(physical_names) != len(set(physical_names)):
            raise RuntimeError("Duplicate physical headers in _FIELDS_MAP.")


# Ejecutar en import-time
RowLegacyMapper._validate_field_map_definition()
