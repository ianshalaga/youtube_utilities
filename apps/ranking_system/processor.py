from enum import Enum
from typing import Callable, Dict, Iterable

from sqlalchemy.orm import Session

from services.ranking.providers.db_provider import RankingDBProvider
from services.ranking.filters import RankingQuery

from domain.ranking.engine.ranking_engine import RankingEngine
from domain.ranking.engine.state import CompetitiveState

from domain.ranking.entities.ranking_entity import RankingEntity

from domain.ranking.stats.base_stats import BaseRankingStats
from domain.ranking.stats.player_stats import PlayerRankingStats
from domain.ranking.stats.team_stats import TeamRankingStats
from domain.ranking.stats.character_stats import CharacterRankingStats
from domain.ranking.stats.player_character_stats import (
    PlayerCharacterRankingStats,
)

from services.ranking.storage.repository import RankingRepository


# ─────────────────────────────────────────────────────────────
# Configuración del ranking
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
# API pública
# ─────────────────────────────────────────────────────────────

def run_ranking(
    *,
    session: Session,
    entity: RankingEntity | str,
    query: RankingQuery,
) -> Dict[int, BaseRankingStats]:
    """
    Ejecuta un ranking según la entidad solicitada y la query.
    """

    entity = RankingEntity(entity)

    repository = RankingRepository()
    provider = RankingDBProvider(
        session=session,
        repository=repository,
    )

    engine = RankingEngine(
        lvl_params=(
            LVL_PARAMS_BATTLES
            if entity in {
                RankingEntity.CHARACTER,
                RankingEntity.PLAYER_CHARACTER,
            }
            else LVL_PARAMS_DUELS
        ),
        k_rating=K_RATING,
        consistency_C=CONSISTENCY_C,
    )

    handler = _ENTITY_HANDLERS.get(entity)

    if handler is None:
        raise ValueError(f"Entidad de ranking no soportada: {entity}")

    return handler(
        provider=provider,
        engine=engine,
        query=query,
    )


# ─────────────────────────────────────────────────────────────
# Handlers por entidad
# ─────────────────────────────────────────────────────────────

def _rank_players(
    *,
    provider: RankingDBProvider,
    engine: RankingEngine,
    query: RankingQuery,
) -> Dict[int, PlayerRankingStats]:
    duels = provider.iter_duels(query)
    return engine.rank_duels(
        duel_events=duels,
        stats_factory=_player_stats_factory,
    )


def _rank_teams(
    *,
    provider: RankingDBProvider,
    engine: RankingEngine,
    query: RankingQuery,
) -> Dict[int, TeamRankingStats]:
    duels = provider.iter_duels(query)
    return engine.rank_duels(
        duel_events=duels,
        stats_factory=_team_stats_factory,
    )


def _rank_characters(
    *,
    provider: RankingDBProvider,
    engine: RankingEngine,
    query: RankingQuery,
) -> Dict[int, CharacterRankingStats]:
    battles = provider.iter_battles(query)
    return engine.rank_battles(
        battle_events=battles,
        entity_key_fn=lambda p: p.game_character_id,
        stats_factory=_character_stats_factory,
    )


def _rank_player_characters(
    *,
    provider: RankingDBProvider,
    engine: RankingEngine,
    query: RankingQuery,
) -> Dict[int, PlayerCharacterRankingStats]:
    battles = provider.iter_battles(query)
    return engine.rank_battles(
        battle_events=battles,
        entity_key_fn=lambda p: (p.player_id, p.game_character_id),
        stats_factory=_player_character_stats_factory,
    )


_ENTITY_HANDLERS: Dict[
    RankingEntity,
    Callable[..., Dict[int, BaseRankingStats]],
] = {
    RankingEntity.PLAYER: _rank_players,
    RankingEntity.TEAM: _rank_teams,
    RankingEntity.CHARACTER: _rank_characters,
    RankingEntity.PLAYER_CHARACTER: _rank_player_characters,
}


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
