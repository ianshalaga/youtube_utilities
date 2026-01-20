from abc import ABC, abstractmethod


class DataLoader(ABC):
    @abstractmethod
    def load(self) -> None:
        """
        Importa datos a la base de datos.
        """
        pass
