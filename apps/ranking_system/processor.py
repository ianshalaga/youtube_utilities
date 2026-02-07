"""
Processor principal del sistema de ranking.

Conecta:
- resolvers (humano → IDs)
- query presets
- provider de DB
- ranking engine
"""

from sqlalchemy.orm import Session

from services.ranking.providers.db_provider import RankingDBProvider
from services.ranking.filters import RankingQuery

from apps.ranking_system.resolvers.season_resolver import SeasonResolver
from apps.ranking_system.resolvers.platform_resolver import PlatformResolver

from apps.ranking_system.queries.season_platform_query import (
    SeasonPlatformRankingQuery,
)

from domain.ranking.engine.ranking_engine import RankingEngine
from domain.ranking.stats.player_stats import PlayerRankingStats


# ─────────────────────────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────────────────────────

LVL_PARAMS_DUELS = {
    "k": 0.02,
    "min_factor": 0.90,
    "max_factor": 1.10,
}

K_RATING = 0.02
CONSISTENCY_C = 10


# ─────────────────────────────────────────────────────────────
# Processor
# ─────────────────────────────────────────────────────────────

def run_player_ranking_by_season_and_platform(
    *,
    session: Session,
    season_name: str,
    platform_name: str,
):
    """
    Ejecuta un ranking de jugadores por season y plataforma.
    """

    # ── 1️⃣ Resolver IDs desde nombres humanos ───────────────
    season_id = SeasonResolver(session).by_name(season_name)
    platform_id = PlatformResolver(session).by_name(platform_name)

    # ── 2️⃣ Construir query preset ───────────────────────────
    preset = SeasonPlatformRankingQuery(
        season_id=season_id,
        platform_id=platform_id,
    )

    query: RankingQuery = preset.build()

    # ── 3️⃣ Obtener eventos desde DB ─────────────────────────
    provider = RankingDBProvider(session)

    duel_events = provider.get_duel_events(query)

    if not duel_events:
        print("⚠️ No hay duelos para los filtros indicados")
        return

    # ── 4️⃣ Ejecutar ranking engine ──────────────────────────
    engine = RankingEngine(
        lvl_params=LVL_PARAMS_DUELS,
        k_rating=K_RATING,
        consistency_C=CONSISTENCY_C,
    )

    results = engine.rank_duels(
        duel_events=duel_events,
        stats_factory=lambda player_id, state, win_rate, score:
            PlayerRankingStats(
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
    )

    # ── 5️⃣ Export simple (CSV / stdout) ─────────────────────
    _print_player_ranking(results)


# ─────────────────────────────────────────────────────────────
# Output helpers
# ─────────────────────────────────────────────────────────────

def _print_player_ranking(results: dict[int, PlayerRankingStats]) -> None:
    """
    Imprime ranking ordenado por score.
    """

    ordered = sorted(
        results.values(),
        key=lambda r: r.score,
        reverse=True,
    )

    print(
        "player_id,events,wins,losses,draws,win_rate,raw_score,score,rating"
    )

    for r in ordered:
        print(
            f"{r.player_id},"
            f"{r.events_played},"
            f"{r.wins},"
            f"{r.losses},"
            f"{r.draws},"
            f"{r.win_rate:.4f},"
            f"{r.raw_score:.2f},"
            f"{r.score:.2f},"
            f"{r.rating:.2f}"
        )
