from abc import ABC, abstractmethod


class RoundScoringStrategy(ABC):

    @abstractmethod
    def valid_codes(self) -> set[str]:
        ...

    @abstractmethod
    def is_win(self, code: str) -> bool:
        ...

    @abstractmethod
    def is_loss(self, code: str) -> bool:
        ...

    @abstractmethod
    def is_draw(self, code: str) -> bool:
        ...

    @abstractmethod
    def score_value(self, code: str) -> float:
        ...
