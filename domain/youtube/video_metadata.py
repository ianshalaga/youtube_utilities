"""
Objeto de dominio: VideoMetadata.

NOTAS DE IMPLEMENTACIÓN PARA EL DESARROLLADOR
---------------------------------------------

- Este módulo pertenece exclusivamente al dominio de la aplicación YouTube.
- No debe contener dependencias de SQLAlchemy, YouTube Data API, filesystem,
  configuración, logging ni otras infraestructuras.
- VideoMetadata representa el conjunto de metadata asociado a un vídeo.
- El mismo tipo se utiliza para representar tanto la metadata actual del vídeo
  como la metadata deseada.
- La distinción entre metadata actual y metadata deseada pertenece a Video,
  que mantiene ambas instancias de VideoMetadata.
- `playlists` contiene IDs de playlists de YouTube, no nombres.
- `game` es deliberadamente un `str` y no debe relacionarse con el modelo
  Game del dominio de ranking.
- `tags` y `thumbnail` son opcionales porque son los únicos campos opcionales
  definidos actualmente por el AlbumManifest.
- Los valores booleanos `made_for_kids` y `contains_synthetic_media` deben
  representar siempre un estado explícito.
- Este objeto no debe realizar validaciones contra las restricciones de la
  YouTube Data API. Las reglas de validación pertenecen al mecanismo de
  validación correspondiente.
- Este objeto tampoco debe determinar qué operaciones deben ejecutarse.
  Esa responsabilidad pertenece a la fase de planificación.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


class VideoMetadata:
    """
    Representa la metadata de un vídeo.

    VideoMetadata puede representar tanto la metadata actualmente existente
    en YouTube como la metadata que la aplicación pretende establecer.

    Attributes:
        title: Título del vídeo.
        description: Descripción del vídeo.
        tags: Tags del vídeo, o None si no se han especificado.
        playlists: IDs de las playlists de YouTube.
        game: Nombre del videojuego asociado al vídeo.
        made_for_kids: Indica si el vídeo está marcado como contenido creado
            para niños.
        contains_synthetic_media: Indica si el vídeo contiene contenido
            sintético o alterado que deba declararse.
        publish_at: Fecha y hora en la que debe publicarse el vídeo.
        thumbnail: Referencia a la miniatura del vídeo, o None si no se ha
            especificado.
    """

    def __init__(
        self,
        title: str,
        description: str,
        tags: list[str] | None,
        playlists: list[str],
        game: str,
        made_for_kids: bool,
        contains_synthetic_media: bool,
        publish_at: datetime,
        thumbnail: Path | None,
    ) -> None:
        """
        Inicializa la metadata de un vídeo.

        Args:
            title: Título del vídeo.
            description: Descripción del vídeo.
            tags: Tags del vídeo. None indica que no se han especificado.
            playlists: IDs de las playlists de YouTube.
            game: Nombre del videojuego asociado.
            made_for_kids: Estado de la declaración de contenido creado para
                niños.
            contains_synthetic_media: Estado de la declaración de contenido
                sintético o alterado.
            publish_at: Fecha y hora de publicación.
            thumbnail: Referencia a la miniatura. None indica que no se ha
                especificado.
        """
        if len(title) > 100:
            raise ValueError("Video title must not exceed 100 characters.")

        if len(description) > 5000:
            raise ValueError("Video description must not exceed 5000 characters.")
        
        self._title = title
        self._description = description
        self._tags = list(tags) if tags is not None else None
        self._playlists = list(playlists)
        self._game = game
        self._made_for_kids = made_for_kids
        self._contains_synthetic_media = contains_synthetic_media
        self._publish_at = publish_at
        self._thumbnail = thumbnail

    @property
    def title(self) -> str:
        return self._title

    @property
    def description(self) -> str:
        return self._description

    @property
    def tags(self) -> tuple[str, ...] | None:
        return tuple(self._tags) if self._tags is not None else None

    @property
    def playlists(self) -> tuple[str, ...]:
        return tuple(self._playlists)

    @property
    def game(self) -> str:
        return self._game

    @property
    def made_for_kids(self) -> bool:
        return self._made_for_kids

    @property
    def contains_synthetic_media(self) -> bool:
        return self._contains_synthetic_media

    @property
    def publish_at(self) -> datetime:
        return self._publish_at

    @property
    def thumbnail(self) -> Path | None:
        return self._thumbnail