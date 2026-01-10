from pathlib import Path
from abc import ABC

from services.media.media_provider import MediaProvider


class Media(ABC):
    def __init__(self, path: Path, media_provider: MediaProvider):
        self._path = path
        self._media_provider = media_provider

    @property
    def name(self) -> str:
        return self.path.stem

    @property
    def path(self) -> Path:
        return self._path

    @property
    def duration(self) -> float:
        return self._media_provider.duration(self.path)
