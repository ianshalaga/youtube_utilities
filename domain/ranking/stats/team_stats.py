from dataclasses import dataclass
from domain.ranking.stats.base_stats import BaseRankingStats


@dataclass(frozen=True)
class TeamRankingStats(BaseRankingStats):
    team_id: int
