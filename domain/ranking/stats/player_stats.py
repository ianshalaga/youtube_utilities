from dataclasses import dataclass
from domain.ranking.stats.base_stats import BaseRankingStats


@dataclass(frozen=True)
class PlayerRankingStats(BaseRankingStats):
    player_id: int
