from pathlib import Path
from math import ceil


class OutputDirectoryPartitioner:
    """
    Calcula rutas de subdirectorios numerados cuando la cantidad
    de elementos excede un máximo permitido por directorio.
    """

    def __init__(self, max_items_per_dir: int):
        if max_items_per_dir <= 0:
            raise ValueError("max_items_per_dir must be > 0")

        self._max_items_per_dir = max_items_per_dir

    def total_subdirs(self, total_items: int) -> int:
        return ceil(total_items / self._max_items_per_dir)

    def padding(self, total_items: int) -> int:
        return len(str(self.total_subdirs(total_items)))

    def get_output_dir(
        self,
        *,
        index: int,
        total_items: int,
        root_dir: Path
    ) -> Path:
        """
        Devuelve el directorio de salida correspondiente a un índice.

        Args:
            index:
                Índice base 0 del elemento.
            total_items:
                Cantidad total de elementos.
            root_dir:
                Directorio raíz de salida.

        Returns:
            Ruta al subdirectorio correcto.
        """
        if total_items <= self._max_items_per_dir:
            return root_dir

        padding = self.padding(total_items)
        subdir_number = (index // self._max_items_per_dir) + 1

        return root_dir / f"{subdir_number:0{padding}d}"
