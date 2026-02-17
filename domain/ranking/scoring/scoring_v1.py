from domain.ranking.scoring.base import RoundScoringStrategy


class RoundScoringV1(RoundScoringStrategy):

    _PERFECT_WIN = {"PW"}
    _PERFECT_LOSS = {"PL"}
    _WIN = {"W"}
    _LOSS = {"LB", "LY"}
    _DRAW = {"D"}

    _SCORE_MAP = {
        "W": 240,
        "PW": 240,
        "LB": 84,
        "LY": 168,
        "PL": 0,
        "D": 240,
    }

    def valid_codes(self):
        return set(self._SCORE_MAP.keys())

    def is_perfect_win(self, code: str) -> bool:
        return code in self._PERFECT_WIN

    def is_perfect_loss(self, code: str) -> bool:
        return code in self._PERFECT_LOSS

    def is_win(self, code: str) -> bool:
        return code in self._WIN

    def is_loss(self, code: str) -> bool:
        return code in self._LOSS

    def is_draw(self, code: str) -> bool:
        return code in self._DRAW

    def score_value(self, code: str) -> float:
        return self._SCORE_MAP[code]
