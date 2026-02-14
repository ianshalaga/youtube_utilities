from dataclasses import dataclass
from datetime import date
from typing import Optional, List

from services.ranking.loaders.legacy import RowLegacyMapper


@dataclass(frozen=True)
class LegacyRowDTO:

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
    duel_order: int
    individual_duel_type: str
    duel_video: Optional[str]
    combat_order: int
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
    team_duel_order: Optional[int]
    team_duel_type: Optional[str]
    # Round
    rounds_p1: tuple[str, ...]
    rounds_p2: tuple[str, ...]

    @classmethod
    def from_mapper(cls, mapper: RowLegacyMapper) -> "LegacyRowDTO":
        if mapper.event_date is None:
            raise ValueError("event_date is required.")

        if mapper.duel_order is None:
            raise ValueError("duel_order is required.")

        if mapper.combat_order is None:
            raise ValueError("combat_order is required.")

        # Convert rounds (ignore None)
        rounds_p1 = []
        rounds_p2 = []

        for i in range(1, 6):
            r1 = mapper.round_result(i, 1)
            r2 = mapper.round_result(i, 2)

            if r1 is None and r2 is None:
                continue

            if (r1 is None) != (r2 is None):
                raise ValueError(
                    f"Inconsistent round data at round {i}."
                )

            rounds_p1.append(r1)
            rounds_p2.append(r2)

        rounds_p1 = tuple(rounds_p1)
        rounds_p2 = tuple(rounds_p2)

        try:
            event_date = date.fromisoformat(mapper.event_date)
        except ValueError:
            raise ValueError(
                f"Invalid ISO date format: {mapper.event_date}")

        dto = cls(
            # Context
            game_name=mapper.game_name,
            game_version=mapper.game_version,
            event_platform=mapper.event_platform,
            region_name=mapper.region_name,
            # Season / Event
            season_name=mapper.season_name,
            event_name=mapper.event_name,
            event_date=event_date,
            event_brackets=mapper.event_brackets,
            event_playlist=mapper.event_playlist,
            # Duel
            duel_order=int(mapper.duel_order),
            individual_duel_type=mapper.individual_duel_type,
            duel_video=mapper.duel_video,
            combat_order=int(mapper.combat_order),
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
            team_duel_order=(
                int(mapper.team_duel_order)
                if mapper.team_duel_order is not None
                else None
            ),
            team_duel_type=mapper.team_duel_type,
            # Round
            rounds_p1=rounds_p1,
            rounds_p2=rounds_p2,
        )

        dto._validate_structural_consistency()
        return dto

    def _validate_structural_consistency(self):
        if not self.rounds_p1 or not self.rounds_p2:
            raise ValueError("Battle must contain at least one round.")

        if len(self.rounds_p1) != len(self.rounds_p2):
            raise ValueError("Round results length mismatch.")

        if len(self.rounds_p1) > 5:
            raise ValueError("Legacy format supports maximum 5 rounds.")

        if self.duel_order <= 0:
            raise ValueError("duel_order must be positive.")

        if self.team_duel_order is not None and self.team_duel_order <= 0:
            raise ValueError("team_duel_order must be positive.")

        if self.combat_order <= 0:
            raise ValueError("combat_order must be positive.")

        if self.individual_duel_type is None:
            raise ValueError("individual_duel_type is required.")

        if (self.player_1_team is None) != (self.player_2_team is None):
            raise ValueError("Both players must have team or neither.")

        if (self.team_duel_order is None) != (self.team_duel_type is None):
            raise ValueError(
                "team_duel_order and team_duel_type must be both set or both None.")

        if any(r is None for r in self.rounds_p1):
            raise ValueError("Round result cannot be None.")

        if any(r is None for r in self.rounds_p2):
            raise ValueError("Round result cannot be None.")

        # if self.player_1_name == self.player_2_name:
        #     raise ValueError("A player cannot fight against themselves.")
