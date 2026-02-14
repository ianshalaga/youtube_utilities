class RowV2Mapper:
    """
    Mapeador de filas CSV v2.

    Responsabilidad:
    - Resolver encabezados canónicos del CSV v2
    - Normalizar strings
    - Exponer propiedades semánticas
    - NO parsea dominio
    - NO accede a DB
    """

    FIELD_MAP = {
        "season_name": ["season"],
        "event_name": ["event"],
        "event_date": ["date"],
        "region_name": ["region"],
        "event_type": ["event_type"],

        "duel_order": ["duel_order"],
        "duel_type": ["duel_type"],
        "duel_video": ["duel_video"],

        "battle_order": ["battle_order"],
        "stage_name": ["stage"],

        "round_order": ["round_order"],

        "player_1_name": ["p1_name"],
        "player_2_name": ["p2_name"],

        "character_1_name": ["p1_character"],
        "character_2_name": ["p2_character"],

        "player_1_result": ["p1_result"],
        "player_2_result": ["p2_result"],

        "player_1_country": ["p1_country"],
        "player_2_country": ["p2_country"],

        "player_1_team": ["p1_team"],
        "player_2_team": ["p2_team"],

        "game_name": ["game"],
        "game_version": ["version"],
        "platform_name": ["platform"],

        "notes": ["notes"],
        "source": ["source"],
    }

    def __init__(self, row: dict[str, str]):
        self._row = row

    def _get(self, logical_name: str) -> str | None:
        for header in self.FIELD_MAP.get(logical_name, []):
            if header in self._row:
                value = self._row.get(header)
                if value is not None:
                    value = value.strip()
                    return value if value != "" else None
        return None

    # --- Event / Season ---
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
    def region_name(self):
        return self._get("region_name")

    @property
    def event_type(self):
        return self._get("event_type")

    # --- Duel ---
    @property
    def duel_order(self):
        return self._get("duel_order")

    @property
    def duel_type(self):
        return self._get("duel_type")

    @property
    def duel_video(self):
        return self._get("duel_video")

    # --- Battle / Round ---
    @property
    def battle_order(self):
        return self._get("battle_order")

    @property
    def stage_name(self):
        return self._get("stage_name")

    @property
    def round_order(self):
        return self._get("round_order")

    # --- Player 1 ---
    @property
    def player_1_name(self):
        return self._get("player_1_name")

    @property
    def character_1_name(self):
        return self._get("character_1_name")

    @property
    def player_1_result(self):
        return self._get("player_1_result")

    @property
    def player_1_country(self):
        return self._get("player_1_country")

    @property
    def player_1_team(self):
        return self._get("player_1_team")

    # --- Player 2 ---
    @property
    def player_2_name(self):
        return self._get("player_2_name")

    @property
    def character_2_name(self):
        return self._get("character_2_name")

    @property
    def player_2_result(self):
        return self._get("player_2_result")

    @property
    def player_2_country(self):
        return self._get("player_2_country")

    @property
    def player_2_team(self):
        return self._get("player_2_team")

    # --- Game ---
    @property
    def game_name(self):
        return self._get("game_name")

    @property
    def game_version(self):
        return self._get("game_version")

    @property
    def platform_name(self):
        return self._get("platform_name")

    # --- Metadata ---
    @property
    def notes(self):
        return self._get("notes")

    @property
    def source(self):
        return self._get("source")
