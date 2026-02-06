from dataclasses import dataclass
from domain.ranking.stats.base_stats import BaseRankingStats


@dataclass(frozen=True)
class PlayerCharacterRankingStats(BaseRankingStats):
    player_id: int
    character_id: int
