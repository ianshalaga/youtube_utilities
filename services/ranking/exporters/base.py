from abc import ABC, abstractmethod
from pathlib import Path


class DataExporter(ABC):

    @abstractmethod
    def export(self, output_path: Path) -> None:
        """
        Exporta datos desde la base de datos
        hacia un formato externo.
        """
        pass
