from dataclasses import dataclass, fields
from datetime import date, datetime
from typing import Optional, Tuple, get_origin, get_args, ClassVar
from types import UnionType

from services.ranking.loaders.legacy import RowLegacyMapper


@dataclass(frozen=True)
class RowLegacyDTO:
    _REQUIRED_FIELDS: ClassVar[tuple[str, ...]]

    # Context
    game_name: str
    game_version: str
    event_platform: str
    region_name: str

    # Season / Event
    season_name: str
    event_name: str
    event_date: date
    event_brackets: Optional[str]
    event_playlist: Optional[str]

    # Duel
    normal_duel_order: int
    normal_duel_type: str
    duel_video: Optional[str]

    # Battle
    combat_order: int
    player_1_name: str
    player_2_name: str
    character_1_name: str
    character_2_name: str
    player_1_country: str
    player_2_country: str
    stage_name: str

    # Team
    player_1_team: Optional[str]
    player_2_team: Optional[str]
    team_duel_order: Optional[int]
    team_duel_type: Optional[str]

    # Round
    rounds_p1: Tuple[str, ...]
    rounds_p2: Tuple[str, ...]

    @classmethod
    def from_mapper(cls, mapper: RowLegacyMapper) -> "RowLegacyDTO":
        # Convert rounds
        rounds_p1 = []
        rounds_p2 = []

        for i in range(1, 6):
            r1 = mapper.round_result(i, 1)
            r2 = mapper.round_result(i, 2)

            if (r1 is None) and (r2 is None):
                raise ValueError(f"Round {i} is missing.")

            if (r1 is None) or (r2 is None):
                raise ValueError(
                    f"Inconsistent round data at round {i}."
                )

            if r1 != "0":
                rounds_p1.append(r1)

            if r2 != "0":
                rounds_p2.append(r2)

        rounds_p1 = tuple(rounds_p1)
        rounds_p2 = tuple(rounds_p2)

        dto = cls(
            # Context
            game_name=mapper.game_name,
            game_version=mapper.game_version,
            event_platform=mapper.event_platform,
            region_name=mapper.region_name,

            # Season / Event
            season_name=mapper.season_name,
            event_name=mapper.event_name,
            event_date=cls._parse_date(mapper.event_date),
            event_brackets=mapper.event_brackets,
            event_playlist=mapper.event_playlist,

            # Duel
            normal_duel_order=cls._to_int(mapper.normal_duel_order),
            normal_duel_type=mapper.normal_duel_type,
            duel_video=mapper.duel_video,
            combat_order=cls._to_int(mapper.combat_order),

            # Battle
            player_1_name=mapper.player_1_name,
            player_2_name=mapper.player_2_name,
            character_1_name=mapper.character_1_name,
            character_2_name=mapper.character_2_name,
            player_1_country=mapper.player_1_country,
            player_2_country=mapper.player_2_country,
            stage_name=mapper.stage_name,

            # Team
            player_1_team=mapper.player_1_team,
            player_2_team=mapper.player_2_team,
            team_duel_order=cls._to_int(mapper.team_duel_order, nullable=True),
            team_duel_type=mapper.team_duel_type,

            # Round
            rounds_p1=rounds_p1,
            rounds_p2=rounds_p2,
        )

        dto._validate_required_fields()
        dto._validate_structural_consistency()
        return dto

    def _validate_structural_consistency(self):
        if len(self.rounds_p1) != len(self.rounds_p2):
            raise ValueError("Round results length mismatch.")

        if len(self.rounds_p1) > 5 or len(self.rounds_p1) < 3:
            raise ValueError("Round results length must be between 3 and 5.")

        if len(self.rounds_p2) > 5 or len(self.rounds_p2) < 3:
            raise ValueError("Round results length must be between 3 and 5.")

        # Los 4 campos opcionales de equipo deben estar todos o ninguno
        if (self.player_1_team is None) != (self.player_2_team is None):
            raise ValueError("Both players must have team or neither.")

        if (self.team_duel_order is None) != (self.team_duel_type is None):
            raise ValueError(
                "team_duel_order and team_duel_type must be both set or both None.")

        if (self.player_1_team is None) != (self.team_duel_order is None):
            raise ValueError(
                "player_1_team and team_duel_order must be both set or both None.")

        if any(r is None for r in self.rounds_p1):
            raise ValueError("Round result p1 cannot be None.")

        if any(r is None for r in self.rounds_p2):
            raise ValueError("Round result p2 cannot be None.")

    def _validate_required_fields(self):
        for name in self._REQUIRED_FIELDS:
            if getattr(self, name) is None:
                raise ValueError(f"Missing required field: {name}")

    @staticmethod
    def _parse_date(value: str | None) -> date:
        '''
        Las fechas son datos estructurales, no texto libre.
        '''
        if not value:
            raise ValueError("Date is required.")

        value = value.strip()

        formats = (
            "%Y-%m-%d",     # YYYY-MM-DD (ISO 8601) Preferido
            "%Y/%m/%d",     # YYYY/MM/DD
            "%d/%m/%Y",     # DD/MM/YYYY
            "%d-%m-%Y",     # DD-MM-YYYY
        )

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

        raise ValueError(f"Formato de fecha no reconocido: {value}")

    @classmethod
    def _to_int(value: object, *, nullable: bool = False) -> int | None:
        """
        Convierte a int de forma estricta.

        - Si nullable=False (default):
            - None → ValueError
            - Valor inválido → ValueError
        - Si nullable=True:
            - None → None
            - Valor inválido → ValueError
        """

        if value is None:
            if nullable:
                return None
            raise ValueError("Expected integer, got None")

        if isinstance(value, int):
            return value

        if isinstance(value, str):
            value = value.strip()
            if value.lstrip("-").isdigit():
                return int(value)

        raise ValueError(f"Invalid integer value: {value!r}")


def _compute_required_fields():
    return tuple(
        f.name
        for f in fields(RowLegacyDTO)
        if not (
            (
                get_origin(f.type) is UnionType
                and type(None) in get_args(f.type)
            )
            or (
                get_origin(f.type) is not None
                and type(None) in get_args(f.type)
            )
        )
    )


RowLegacyDTO._REQUIRED_FIELDS = _compute_required_fields()
