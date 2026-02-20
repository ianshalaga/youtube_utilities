"""
Row Legacy Mapper
=================

Notas de implementación
-----------------------

Este módulo representa la primera capa del pipeline legacy:

    CSV → Mapper → DTO → Validator → Normalizer → Aggregator → Loader

Responsabilidad del Mapper:

- Adaptar una fila cruda (dict[str, str]) proveniente del CSV.
- Resolver nombres físicos de columnas a nombres lógicos.
- Normalizar strings (strip).
- Encapsular acceso al diccionario interno.
- Validar estructura sintáctica del CSV.

No:
- Realiza validaciones de dominio.
- Convierte a tipos Python fuertes (eso corresponde al DTO).
- Deriva información.
- Accede a base de datos.
- Persiste información.

Este componente es puramente estructural.
"""


"""
Descripción general
-------------------

RowLegacyMapper es un wrapper elegante sobre una fila CSV.

Su función es desacoplar:

    - La representación física del CSV
    - De la representación lógica utilizada por el sistema

Mediante el uso de _FIELDS_MAP, el sistema puede cambiar nombres
de columnas físicas sin afectar las capas superiores.

El Mapper valida únicamente:

- Fila vacía.
- Headers faltantes.
- Headers inesperados.
- Duplicidad en definición de campos físicos.

No realiza validación semántica.
"""


class RowLegacyMapper:
    """
    Adaptador estructural de una fila CSV legacy.

    Encapsula:
    - El acceso al diccionario crudo.
    - La resolución de nombres lógicos.
    - La normalización básica de strings.

    Es inmutable en comportamiento (no modifica la fila original).
    """

    # Mapeo lógico → físico.
    # Clave: nombre utilizado internamente por el sistema.
    # Valor: nombre real de la columna en el CSV.
    _FIELDS_MAP = {

        # --- Context ---
        "game_name": "game",
        "game_version": "version",
        "event_platform": "platform",
        "region_name": "region",

        # --- Season / Event ---
        "season_name": "season",
        "event_name": "event",
        "event_date": "date",
        "event_brackets": "brackets",
        "event_playlist": "playlist",

        # --- Duel ---
        "normal_duel_order": "duel",
        "normal_duel_type": "duel_type",
        "duel_video": "video",
        "combat_order": "combat",

        # --- Battle ---
        "player_1_name": "player1",
        "player_2_name": "player2",
        "character_1_name": "character1",
        "character_2_name": "character2",
        "player_1_country": "p1_country",
        "player_2_country": "p2_country",
        "stage_name": "stage",

        # --- Team ---
        "player_1_team": "p1_team",
        "player_2_team": "p2_team",
        "team_duel_order": "team_duel",
        "team_duel_type": "t_duel_type",

        # --- Round ---
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

    # ---------------------------------------------------------

    def __init__(self, row: dict[str, str]):
        """
        Inicializa el mapper con una fila cruda.

        Parámetros:
            row: diccionario representando una fila CSV.

        Valida inmediatamente la estructura de headers.
        """
        self._row = row
        self._validate_row_headers()

    # ---------------------------------------------------------

    def _get(self, logical_name: str):
        """
        Obtiene el valor asociado a un nombre lógico.

        - Resuelve el header físico correspondiente.
        - Aplica strip().
        - Convierte strings vacíos a None.
        - No convierte tipos.

        Retorna:
            str | None
        """
        header = self._FIELDS_MAP[logical_name]
        value = self._row.get(header)

        # Header faltante ya fue validado en constructor.
        if value is None:
            return None

        value_strip = value.strip()

        # Convierte string vacío a None
        return value_strip if value_strip else None

    # ---------------------------------------------------------

    def _validate_row_headers(self):
        """
        Valida coherencia estructural de la fila.

        Reglas:
        - La fila no puede estar vacía.
        - No deben faltar headers esperados.
        - No deben existir headers inesperados.
        """

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

    # =========================================================
    # Context
    # =========================================================

    @property
    def game_name(self):
        """Nombre del juego."""
        return self._get("game_name")

    @property
    def game_version(self):
        """Versión del juego."""
        return self._get("game_version")

    @property
    def event_platform(self):
        """Plataforma del evento."""
        return self._get("event_platform")

    @property
    def region_name(self):
        """Región del evento."""
        return self._get("region_name")

    # =========================================================
    # Season / Event
    # =========================================================

    @property
    def season_name(self):
        """Nombre de la temporada."""
        return self._get("season_name")

    @property
    def event_name(self):
        """Nombre del evento."""
        return self._get("event_name")

    @property
    def event_date(self):
        """Fecha del evento en formato crudo (string)."""
        return self._get("event_date")

    @property
    def event_brackets(self):
        """URL de brackets si existe."""
        return self._get("event_brackets")

    @property
    def event_playlist(self):
        """URL de playlist si existe."""
        return self._get("event_playlist")

    # =========================================================
    # Duel
    # =========================================================

    @property
    def normal_duel_order(self):
        """Orden del duelo dentro del evento."""
        return self._get("normal_duel_order")

    @property
    def normal_duel_type(self):
        """Tipo de duelo."""
        return self._get("normal_duel_type")

    @property
    def duel_video(self):
        """URL del video del duelo si existe."""
        return self._get("duel_video")

    @property
    def combat_order(self):
        """Orden de la batalla dentro del duelo."""
        return self._get("combat_order")

    # =========================================================
    # Battle
    # =========================================================

    @property
    def player_1_name(self):
        """Nombre del jugador 1."""
        return self._get("player_1_name")

    @property
    def player_2_name(self):
        """Nombre del jugador 2."""
        return self._get("player_2_name")

    @property
    def character_1_name(self):
        """Personaje del jugador 1."""
        return self._get("character_1_name")

    @property
    def character_2_name(self):
        """Personaje del jugador 2."""
        return self._get("character_2_name")

    @property
    def player_1_country(self):
        """País del jugador 1."""
        return self._get("player_1_country")

    @property
    def player_2_country(self):
        """País del jugador 2."""
        return self._get("player_2_country")

    @property
    def stage_name(self):
        """Nombre del stage."""
        return self._get("stage_name")

    # =========================================================
    # Team
    # =========================================================

    @property
    def player_1_team(self):
        """Equipo del jugador 1 si existe."""
        return self._get("player_1_team")

    @property
    def player_2_team(self):
        """Equipo del jugador 2 si existe."""
        return self._get("player_2_team")

    @property
    def team_duel_order(self):
        """Orden del duelo de equipo si existe."""
        return self._get("team_duel_order")

    @property
    def team_duel_type(self):
        """Tipo de duelo de equipo si existe."""
        return self._get("team_duel_type")

    # =========================================================
    # Round
    # =========================================================

    def round_result(self, round_number: int, player: int) -> str | None:
        """
        Devuelve el resultado de un round para un jugador específico.

        Parámetros:
            round_number: entero entre 1 y 5.
            player: 1 o 2.

        Retorna:
            str | None

        Lanza:
            ValueError si round_number o player son inválidos.
        """

        if player not in (1, 2):
            raise ValueError(f"Invalid player index: {player}")

        if round_number not in (1, 2, 3, 4, 5):
            raise ValueError(f"Invalid round number: {round_number}")

        key = f"round_{round_number}_p{player}"
        return self._get(key)

    # ---------------------------------------------------------

    @classmethod
    def _validate_fields_map_definition(cls):
        """
        Valida que no existan nombres físicos duplicados
        en la definición de _FIELDS_MAP.

        Se ejecuta en tiempo de importación.
        """
        physical_names = list(cls._FIELDS_MAP.values())

        if len(physical_names) != len(set(physical_names)):
            raise RuntimeError("Duplicate physical names in _FIELDS_MAP.")


# Validación en tiempo de importación
RowLegacyMapper._validate_fields_map_definition()
