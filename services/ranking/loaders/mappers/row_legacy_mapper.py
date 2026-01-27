class RowLegacyMapper:
    """
    Mapeador de filas CSV legacy.

    Responsabilidad:
    - Resolver nombres alternativos de columnas
    - Normalizar strings
    - NO parsea dominio
    - NO accede a DB
    """

    FIELD_MAP = {
        "season_name": ["season"],
        "event_name": ["event"],
        "event_date": ["date"],
        "event_brackets": ["brackets"],
        "event_playlist": ["playlist"],
        "region_name": ["region"],
        "event_platform": ["platform"],
        "game_name": ["game"],
        "game_version": ["version"],
        "duel_order": ["duel"],
        "duel_type": ["duel_type"],
        "duel_video": ["video"],
        "combat_order": ["combat"],
        "player_1_name": ["player1"],
        "player_2_name": ["player2"],
        "character_1_name": ["character1"],
        "character_2_name": ["character2"],
        "country_player_1": ["p1_country"],
        "country_player_2": ["p2_country"],
        "team_player_1": ["p1_team"],
        "team_player_2": ["p2_team"],
        "stage_name": ["stage"],
        "round_1_p1": ["r1_p1"],
        "round_2_p1": ["r2_p1"],
        "round_3_p1": ["r3_p1"],
        "round_4_p1": ["r4_p1"],
        "round_5_p1": ["r5_p1"],
        "round_1_p2": ["r1_p2"],
        "round_2_p2": ["r2_p2"],
        "round_3_p2": ["r3_p2"],
        "round_4_p2": ["r4_p2"],
        "round_5_p2": ["r5_p2"],
    }

    def __init__(self, row: dict[str, str]):
        self._row = row

    def _get(self, logical_name: str):
        for header in self.FIELD_MAP.get(logical_name, []):
            if header in self._row:
                value = self._row.get(header)
                if value:
                    return value.strip()
        return None

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

    @property
    def region_name(self):
        return self._get("region_name")

    @property
    def event_platform(self):
        return self._get("event_platform")

    @property
    def game_name(self):
        return self._get("game_name")

    @property
    def game_version(self):
        return self._get("game_version")

    @property
    def duel_order(self):
        return self._get("duel_order")

    @property
    def duel_type(self):
        return self._get("duel_type")

    @property
    def duel_video(self):
        return self._get("duel_video")

    @property
    def combat_order(self):
        return self._get("combat_order")

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
    def country_player_1(self):
        return self._get("country_player_1")

    @property
    def country_player_2(self):
        return self._get("country_player_2")

    @property
    def team_player_1(self):
        return self._get("team_player_1")

    @property
    def team_player_2(self):
        return self._get("team_player_2")

    @property
    def stage_name(self):
        return self._get("stage_name")

    @property
    def round_1_p1(self):
        return self._get("round_1_p1")

    @property
    def round_2_p1(self):
        return self._get("round_2_p1")

    @property
    def round_3_p1(self):
        return self._get("round_3_p1")

    @property
    def round_4_p1(self):
        return self._get("round_4_p1")

    @property
    def round_5_p1(self):
        return self._get("round_5_p1")

    @property
    def round_1_p2(self):
        return self._get("round_1_p2")

    @property
    def round_2_p2(self):
        return self._get("round_2_p2")

    @property
    def round_3_p2(self):
        return self._get("round_3_p2")

    @property
    def round_4_p2(self):
        return self._get("round_4_p2")

    @property
    def round_5_p2(self):
        return self._get("round_5_p2")
