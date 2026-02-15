from dataclasses import dataclass
from typing import Optional

from services.ranking.loaders.legacy.row_legacy_dto import LegacyRowDTO


@dataclass(frozen=True)
class NormalizedLegacyRow:

    # Context
    game_name: str
    game_version: str
    event_platform: str
    region_name: str

    # Event
    season_name: str
    event_name: str
    event_date: str
    event_brackets: Optional[str]
    event_playlist: Optional[str]

    # Duel
    duel_sequence_number: int
    individual_duel_type: str
    duel_video: Optional[str]
    battle_sequence_number: int
    is_team_duel: bool

    # Battle
    player_1_name: str
    player_2_name: str
    character_1_name: str
    character_2_name: str
    player_1_country: Optional[str]
    player_2_country: Optional[str]
    stage_name: str

    # Team
    player_1_team: Optional[str]
    player_2_team: Optional[str]
    team_duel_sequence_number: Optional[int]
    team_duel_type: Optional[str]

    # Rounds
    rounds_p1: tuple[str, ...]
    rounds_p2: tuple[str, ...]

    # Derived
    event_type_name: str
    franchise_name: str


class RowLegacyNormalizer:

    @staticmethod
    def normalize(dto: LegacyRowDTO) -> NormalizedLegacyRow:

        return NormalizedLegacyRow(

            # Context
            game_name=RowLegacyNormalizer._normalize_name(dto.game_name),
            game_version=dto.game_version.strip(),
            event_platform=dto.event_platform.strip(),
            region_name=RowLegacyNormalizer._normalize_name(dto.region_name),

            # Event
            season_name=RowLegacyNormalizer._normalize_name(dto.season_name),
            event_name=RowLegacyNormalizer._normalize_name(dto.event_name),
            event_date=dto.event_date.isoformat(),
            event_brackets=RowLegacyNormalizer._clean_optional(
                dto.event_brackets),
            event_playlist=RowLegacyNormalizer._clean_optional(
                dto.event_playlist),

            # Duel
            duel_sequence_number=dto.duel_order,
            duel_type=dto.individual_duel_type.strip(),
            duel_video=RowLegacyNormalizer._clean_optional(dto.duel_video),
            battle_sequence_number=dto.combat_order,
            is_team_duel=dto.team_duel_order is not None,

            # Battle
            player_1_name=RowLegacyNormalizer._normalize_name(
                dto.player_1_name),
            player_2_name=RowLegacyNormalizer._normalize_name(
                dto.player_2_name),
            character_1_name=RowLegacyNormalizer._normalize_name(
                dto.character_1_name),
            character_2_name=RowLegacyNormalizer._normalize_name(
                dto.character_2_name),
            player_1_country=RowLegacyNormalizer._clean_optional(
                dto.player_1_country),
            player_2_country=RowLegacyNormalizer._clean_optional(
                dto.player_2_country),
            stage_name=RowLegacyNormalizer._normalize_name(dto.stage_name),

            # Team
            player_1_team=RowLegacyNormalizer._clean_optional(
                dto.player_1_team),
            player_2_team=RowLegacyNormalizer._clean_optional(
                dto.player_2_team),
            team_duel_sequence_number=dto.team_duel_order,
            team_duel_type=RowLegacyNormalizer._clean_optional(
                dto.team_duel_type),

            # Rounds
            rounds_p1=dto.rounds_p1,
            rounds_p2=dto.rounds_p2,
        )

    @staticmethod
    def _normalize_name(value: str) -> str:
        """
        Canonicaliza nombres:
        - strip
        - Title case
        """
        return value.strip().title()

    @staticmethod
    def _clean_optional(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value if value else None
