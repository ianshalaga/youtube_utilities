from sqlalchemy.orm import Session

from services.ranking.providers.db_provider import RankingDBProvider
from services.ranking.filters import RankingQuery

from domain.ranking.engine.ranking_engine import RankingEngine
from domain.ranking.engine.state import CompetitiveState

from domain.ranking.stats.player_stats import PlayerRankingStats
from domain.ranking.stats.team_stats import TeamRankingStats
from domain.ranking.stats.character_stats import CharacterRankingStats
from domain.ranking.stats.player_character_stats import (
    PlayerCharacterRankingStats,
)


# ─────────────────────────────────────────────────────────────
# Configuración base
# ─────────────────────────────────────────────────────────────

LVL_PARAMS_BATTLES = {
    "k": 0.03,
    "min_factor": 0.85,
    "max_factor": 1.15,
}

LVL_PARAMS_DUELS = {
    "k": 0.02,
    "min_factor": 0.90,
    "max_factor": 1.10,
}

K_RATING = 0.02
CONSISTENCY_C = 10


# ─────────────────────────────────────────────────────────────
# API pública del processor
# ─────────────────────────────────────────────────────────────

def run_ranking(
    *,
    session: Session,
    entity: str,
    query: RankingQuery,
) -> dict:
    """
    Ejecuta un ranking genérico según entidad y query.
    """

    provider = RankingDBProvider(session)
    engine = RankingEngine(
        lvl_params=(
            LVL_PARAMS_BATTLES
            if entity in {"character", "player_character"}
            else LVL_PARAMS_DUELS
        ),
        k_rating=K_RATING,
        consistency_C=CONSISTENCY_C,
    )

    if entity == "player":
        duels = provider.iter_duels(query)
        return engine.rank_duels(
            duel_events=duels,
            stats_factory=_player_stats_factory,
        )

    if entity == "team":
        duels = provider.iter_duels(query)
        return engine.rank_duels(
            duel_events=duels,
            stats_factory=_team_stats_factory,
        )

    if entity == "character":
        battles = provider.iter_battles(query)
        return engine.rank_battles(
            battle_events=battles,
            entity_key_fn=lambda p: p.game_character_id,
            stats_factory=_character_stats_factory,
        )

    if entity == "player_character":
        battles = provider.iter_battles(query)
        return engine.rank_battles(
            battle_events=battles,
            entity_key_fn=lambda p: (p.player_id, p.game_character_id),
            stats_factory=_player_character_stats_factory,
        )

    raise ValueError(f"Entidad de ranking desconocida: {entity}")


# ─────────────────────────────────────────────────────────────
# Factories de stats
# ─────────────────────────────────────────────────────────────

def _player_stats_factory(
    player_id: int,
    state: CompetitiveState,
    win_rate: float,
    score: float,
) -> PlayerRankingStats:
    return PlayerRankingStats(
        player_id=player_id,
        events_played=state.events_played,
        wins=state.wins,
        losses=state.losses,
        draws=state.draws,
        win_rate=win_rate,
        raw_score=state.raw_score,
        score=score,
        rating=state.rating,
    )


def _team_stats_factory(
    team_id: int,
    state: CompetitiveState,
    win_rate: float,
    score: float,
) -> TeamRankingStats:
    return TeamRankingStats(
        team_id=team_id,
        events_played=state.events_played,
        wins=state.wins,
        losses=state.losses,
        draws=state.draws,
        win_rate=win_rate,
        raw_score=state.raw_score,
        score=score,
        rating=state.rating,
    )


def _character_stats_factory(
    character_id: int,
    state: CompetitiveState,
    win_rate: float,
    score: float,
) -> CharacterRankingStats:
    return CharacterRankingStats(
        character_id=character_id,
        events_played=state.events_played,
        wins=state.wins,
        losses=state.losses,
        draws=state.draws,
        win_rate=win_rate,
        raw_score=state.raw_score,
        score=score,
        rating=state.rating,
    )


def _player_character_stats_factory(
    key: tuple[int, int],
    state: CompetitiveState,
    win_rate: float,
    score: float,
) -> PlayerCharacterRankingStats:
    player_id, character_id = key
    return PlayerCharacterRankingStats(
        player_id=player_id,
        character_id=character_id,
        events_played=state.events_played,
        wins=state.wins,
        losses=state.losses,
        draws=state.draws,
        win_rate=win_rate,
        raw_score=state.raw_score,
        score=score,
        rating=state.rating,
    )
