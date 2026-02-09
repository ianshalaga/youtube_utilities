from dataclasses import dataclass
from typing import Optional


def _validate_enum(value, allowed, field_name):
    if value is None:
        return
    if value not in allowed:
        raise ValueError(
            f"{field_name} must be one of {allowed} (got {value})"
        )


@dataclass(frozen=True)
class ScopeFilters:
    season_name: Optional[str]
    event_name: Optional[str]
    event_type_name: Optional[str]
    region_name: Optional[str]
    game_name: Optional[str]
    game_version: Optional[str]
    event_platform: Optional[str]
    game_franchise_name: Optional[str]


@dataclass(frozen=True)
class DuelFilters:
    duel_id: Optional[int]
    duel_type_name: Optional[str]


@dataclass(frozen=True)
class ParticipantFilters:
    player_name: Optional[str]
    team_name: Optional[str]


@dataclass(frozen=True)
class BattleFilters:
    stage_name: Optional[str]
    character_identity_name: Optional[str]
    participant_position: Optional[int]

    def __post_init__(self):
        _validate_enum(
            self.participant_position,
            allowed=(1, 2),
            field_name="participant_position",
        )


@dataclass(frozen=True)
class PlayerFilters:
    country_iso_code: Optional[str]


@dataclass(frozen=True)
class RankingFilters:
    scope: ScopeFilters
    duel: DuelFilters
    participant: ParticipantFilters
    battle: BattleFilters
    player: PlayerFilters
