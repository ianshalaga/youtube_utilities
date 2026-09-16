# domain\youtube\video.py

"""
Entidad de dominio: Video.

NOTAS DE IMPLEMENTACIÓN PARA EL DESARROLLADOR
---------------------------------------------

- Este módulo pertenece exclusivamente al dominio de la aplicación YouTube.
- No debe contener dependencias de SQLAlchemy, YouTube Data API, filesystem,
  configuración, logging ni otras infraestructuras.
- Video representa un vídeo concreto de YouTube perteneciente a un Album.
- Cada Video tiene una posición única dentro del álbum.
- La posición es independiente del título del vídeo. Las compilaciones también
  tienen posición aunque su título no contenga un número.
- Las canciones ocupan las primeras posiciones del álbum según el orden
  definido por el manifest. Las compilaciones ocupan las posiciones siguientes
  según su orden de subida a YouTube.
- VideoType distingue entre canciones y compilaciones.
- `video_id` es el identificador del vídeo en YouTube.
- `metadata` representa el estado que la aplicación pretende
  establecer.
- Las compilaciones conservan su título actual. La construcción de la metadata
  deseada para una compilación debe realizarse antes de construir o actualizar
  este objeto, no mediante lógica específica de la API dentro de Video.
- La comparación entre metadata actual y deseada, así como la determinación de
  operaciones necesarias, pertenece a la fase de planificación.
- Video no debe realizar llamadas a servicios ni modificar remotamente YouTube.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.youtube.video_metadata import VideoMetadata


class VideoType(Enum):
    """
    Define los tipos de vídeo que pueden pertenecer a un álbum.

    Attributes:
        SONG: Vídeo correspondiente a una canción individual del álbum.
        COMPILATION: Vídeo correspondiente a una compilación del álbum.
    """

    SONG = "song"
    COMPILATION = "compilation"


class Video:
    """
    Representa un vídeo concreto de YouTube perteneciente a un álbum.

    Un Video mantiene la identidad del vídeo dentro de YouTube, su posición,
    tipo dentro del álbum y tanto su metadata.

    Attributes:
        video_id: Identificador único del vídeo en YouTube.
        position: Posición del vídeo dentro del álbum.
        video_type: Tipo de vídeo, canción o compilación.
        metadata: Metadata que la aplicación pretende establecer.
    """

    def __init__(
        self,
        video_id: str,
        position: int,
        video_type: VideoType,
        metadata: VideoMetadata,
    ) -> None:
        """
        Inicializa un vídeo.

        Args:
            video_id: Identificador del vídeo en YouTube.
            position: Posición del vídeo dentro del álbum.
            video_type: Tipo de vídeo.
            metadata: Metadata deseada.

        Raises:
            TypeError: Si position no es un entero.
            ValueError: Si position no es mayor que cero.
        """
        if not isinstance(position, int) or isinstance(position, bool):
            raise TypeError("Video position must be an integer.")

        if position <= 0:
            raise ValueError("Video position must be greater than zero.")

        self._video_id = video_id
        self._position = position
        self._video_type = video_type
        self._metadata = metadata

    @property
    def video_id(self) -> str:
        return self._video_id

    @property
    def position(self) -> int:
        return self._position

    @property
    def video_type(self) -> VideoType:
        return self._video_type

    @property
    def metadata(self) -> VideoMetadata:
        return self._metadata


    def __repr__(self) -> str:
        """Devuelve una representación útil del vídeo para depuración."""
        return (
            f"Video("
            f"video_id={self._video_id!r}, "
            f"position={self._position}, "
            f"video_type={self._video_type!r}"
            f")"
        )