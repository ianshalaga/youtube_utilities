from dataclasses import dataclass
from datetime import date
from typing import Optional, Tuple

from domain.ranking.scoring.scoring_v1 import RoundScoringV1
from services.ranking.loaders.legacy.row_legacy_dto import RowLegacyDTO


# =========================
# Aggregate Models
# =========================

@dataclass(frozen=True)
class NormalizedEventContext:
    season_name: str
    region_name: str
    event_type_name: str
    game_name: str
    game_version: str
    platform_name: str
    event_name: str
    event_date: date
    brackets_url: Optional[str]
    playlist_url: Optional[str]


@dataclass(frozen=True)
class NormalizedDuelContext:
    normal_sequence_number: int
    duel_type_name: str
    is_team_duel: bool
    team_sequence_number: Optional[int]
    team_duel_type_name: Optional[str]
    video_url: Optional[str]


@dataclass(frozen=True)
class NormalizedBattleContext:
    battle_sequence_number: int
    stage_name: str
    is_draw: bool
    winner_position: Optional[int]
    loser_position: Optional[int]


@dataclass(frozen=True)
class NormalizedRound:
    sequence_number: int
    p1_code: str
    p2_code: str


@dataclass(frozen=True)
class NormalizedParticipant:
    player_name: str
    character_name: str
    country: str
    team_name: Optional[str]


@dataclass(frozen=True)
class NormalizedBattleAggregate:
    event: NormalizedEventContext
    duel: NormalizedDuelContext
    battle: NormalizedBattleContext
    participants: Tuple[NormalizedParticipant, NormalizedParticipant]
    rounds: Tuple[NormalizedRound, ...]


# =========================
# Normalizer
# =========================

class RowLegacyNormalizer:

    @staticmethod
    def normalize(dto: RowLegacyDTO) -> NormalizedBattleAggregate:

        round_scoring = RoundScoringV1()

        # --- Derive winner ---
        p1_wins = sum(
            1 for r in dto.rounds_p1 if round_scoring.is_win_result(r)
        )
        p2_wins = sum(
            1 for r in dto.rounds_p2 if round_scoring.is_win_result(r)
        )

        if p1_wins == p2_wins:
            is_draw = True
            winner_position = None
            loser_position = None
        elif p1_wins > p2_wins:
            is_draw = False
            winner_position = 1
            loser_position = 2
        else:
            is_draw = False
            winner_position = 2
            loser_position = 1

        # --- Build event ---
        event = NormalizedEventContext(
            game_name=dto.game_name,
            game_version=dto.game_version,
            platform=dto.event_platform,
            region=dto.region_name,
            season=dto.season_name,
            event_name=dto.event_name,
            event_date=dto.event_date,
            brackets_url=dto.event_brackets,
            playlist_url=dto.event_playlist,
        )

        # --- Build duel ---
        is_team_duel = dto.player_1_team is not None

        duel = NormalizedDuelContext(
            duel_order=dto.normal_duel_order,
            duel_type=dto.normal_duel_type,
            is_team_duel=is_team_duel,
            team_duel_order=dto.team_duel_order,
            team_duel_type=dto.team_duel_type,
            video_url=dto.duel_video,
        )

        # --- Build participants ---
        p1 = NormalizedParticipant(
            player_name=dto.player_1_name,
            character_name=dto.character_1_name,
            country=dto.player_1_country,
            team_name=dto.player_1_team,
        )

        p2 = NormalizedParticipant(
            player_name=dto.player_2_name,
            character_name=dto.character_2_name,
            country=dto.player_2_country,
            team_name=dto.player_2_team,
        )

        # --- Build rounds ---
        rounds = tuple(
            NormalizedRound(i + 1, r1, r2)
            for i, (r1, r2) in enumerate(zip(dto.rounds_p1, dto.rounds_p2))
        )

        # --- Build battle ---
        battle = NormalizedBattleContext(
            combat_order=dto.combat_order,
            stage_name=dto.stage_name,
            is_draw=is_draw,
            winner_position=winner_position,
            loser_position=loser_position,
        )

        return NormalizedBattleAggregate(
            event=event,
            duel=duel,
            battle=battle,
            participants=(p1, p2),
            rounds=rounds,
        )
