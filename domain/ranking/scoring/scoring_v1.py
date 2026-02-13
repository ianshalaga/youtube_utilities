from domain.ranking.scoring.base import RoundScoringStrategy


class RoundScoringV1(RoundScoringStrategy):

    _WIN = {"W", "PW"}
    _LOSS = {"LB", "LY", "PL"}
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

    def is_win(self, code: str) -> bool:
        return code in self._WIN

    def is_loss(self, code: str) -> bool:
        return code in self._LOSS

    def is_draw(self, code: str) -> bool:
        return code in self._DRAW

    def score_value(self, code: str) -> float:
        return self._SCORE_MAP[code]
