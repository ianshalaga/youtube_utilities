from enum import Enum


class RankingEntity(str, Enum):
    PLAYER = "player"
    TEAM = "team"
    CHARACTER = "character"
    PLAYER_CHARACTER = "player_character"
