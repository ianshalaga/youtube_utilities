
from dataclasses import dataclass
from domain.ranking.stats.base_stats import BaseRankingStats


@dataclass(frozen=True)
class CharacterRankingStats(BaseRankingStats):
    character_id: int
