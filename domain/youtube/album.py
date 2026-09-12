"""
Entidad de dominio: Album.

NOTAS DE IMPLEMENTACIÓN PARA EL DESARROLLADOR
---------------------------------------------

- Este módulo pertenece exclusivamente al dominio de la aplicación YouTube.
- No debe contener dependencias de SQLAlchemy, YouTube Data API, filesystem,
  configuración, logging ni otras infraestructuras.
- Album representa la unidad de trabajo completa del proceso de gestión.
- Las instancias de Video representan los vídeos reales de YouTube asociados
  al álbum una vez completada la fase de descubrimiento.
- El orden de los vídeos es significativo y está representado mediante la
  propiedad `position` de cada Video.
- Las compilaciones forman parte del mismo álbum que las canciones. La
  distinción entre ambos tipos pertenece a Video, no a una colección
  independiente dentro de Album.
- `game` es deliberadamente un `str`. No debe establecerse ninguna relación
  con el modelo Game del dominio de ranking.
- Los playlist IDs son identificadores de YouTube y se almacenan como strings.
  El dominio no necesita conocer el nombre de las playlists.
- `tags` y `thumbnail` son opcionales porque son los únicos campos opcionales
  definidos actualmente por el AlbumManifest.
- La fecha `first_publish_at` representa la fecha de publicación del primer
  vídeo. Las fechas individuales de publicación se derivan posteriormente
  para cada Video.
- La validación de títulos, descripciones y demás restricciones de YouTube
  NO pertenece a esta entidad. Debe realizarse mediante el mecanismo de
  validación correspondiente.
- La entidad no debe ejecutar operaciones ni modificar remotamente YouTube.
"""

from __future__ import annotations

from domain.youtube.validation import ValidationResult
from domain.youtube.publication_settings import PublicationSettings

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.youtube.video import Video


class Album:
    """
    Representa un álbum completo dentro del flujo de gestión de vídeos.

    Un álbum constituye la unidad de trabajo de la aplicación. Contiene la
    configuración común a sus vídeos y la colección de vídeos de YouTube que
    han sido descubiertos como pertenecientes al álbum.

    Attributes:
        name: Nombre identificativo del álbum.
        description: Descripción que se aplicará al contenido del álbum.
        playlists: IDs de las playlists de YouTube a las que se añadirán
            los vídeos.
        game: Nombre del videojuego asociado al álbum.
        first_publish_at: Fecha y hora de publicación del primer vídeo.
        tags: Tags que se aplicarán a los vídeos, o None si no se han
            especificado.
        thumbnail: Referencia a la miniatura que se utilizará, o None si no
            se ha especificado.
        videos: Vídeos pertenecientes al álbum.
    """

    def __init__(
        self,
        name: str,
        description: str,
        playlists: list[str],
        game: str,
        publication: PublicationSettings,
        tags: list[str] | None = None,
        thumbnail: Path | None = None,
        videos: list[Video] | None = None,
    ) -> None:
        """
        Inicializa un álbum.

        Args:
            name: Nombre identificativo del álbum.
            description: Descripción común del álbum.
            playlists: IDs de las playlists de YouTube.
            game: Nombre del videojuego asociado.
            publication: Fecha y hora de publicación del primer vídeo e intervalo en días.
            tags: Tags comunes a los vídeos. None indica que no se han
                especificado tags.
            thumbnail: Referencia a la miniatura. None indica que no se ha
                especificado una miniatura.
            videos: Vídeos pertenecientes al álbum. Puede omitirse durante
                la construcción inicial y añadirse posteriormente durante
                discovery.
        """

        if len(description) > 5000:
            raise ValueError("Album description must not exceed 5000 characters.")

        self._name = name
        self._description = description
        self._playlists = list(playlists)
        self._game = game
        self._publication = publication
        self._tags = list(tags) if tags is not None else None
        self._thumbnail = thumbnail
        self._videos = list(videos) if videos is not None else []

    def add_video(self, video: Video) -> None:
        """
        Añade un vídeo al álbum.

        El orden de los vídeos se determina por la propiedad `position` del
        propio Video. Este método conserva el orden en el que los vídeos son
        añadidos durante el descubrimiento.

        Args:
            video: Vídeo de YouTube perteneciente al álbum.
        """
        self._videos.append(video)

    @property
    def publication(self) -> PublicationSettings:
        return self._publication

    @property
    def video_count(self) -> int:
        """
        Devuelve el número de vídeos pertenecientes al álbum.

        Returns:
            Número total de vídeos, incluyendo canciones y compilaciones.
        """
        return len(self._videos)

    def __repr__(self) -> str:
        """Devuelve una representación útil del álbum para depuración."""
        return (
            f"Album("
            f"name={self._name!r}, "
            f"video_count={self.video_count}"
            f")"
        )

    def validate(self) -> ValidationResult:
        """Validate the structural integrity of the album."""
        result = ValidationResult()

        positions: dict[int, list[str]] = {}

        for video in self._videos:
            positions.setdefault(video.position, []).append(video.video_id)

        for position, video_ids in positions.items():
            if len(video_ids) > 1:
                result.add_error(
                    field=f"videos.position[{position}]",
                    message=(
                        f"Position {position} is used by multiple videos: "
                        f"{', '.join(video_ids)}."
                    ),
                )

        return result