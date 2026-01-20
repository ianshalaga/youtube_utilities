from abc import ABC, abstractmethod


class DataProvider(ABC):

    @abstractmethod
    def iter_duels(self):
        pass

    @abstractmethod
    def iter_battles(self):
        pass
