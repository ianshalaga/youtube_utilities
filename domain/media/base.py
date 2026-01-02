from pathlib import Path
from abc import ABC, abstractmethod


class Media(ABC):
    def __init__(self, path: Path, probe_provider: MediaProbeProvider):
        self._path = path
        self._probe_provider = probe_provider

    @property
    def name(self) -> str:
        return self.path.stem

    @property
    def path(self) -> Path:
        return self._path

    @property
    def duration(self) -> float:
        return self._probe_provider.duration(self.path)


class MediaProbeProvider(ABC):
    @abstractmethod
    def duration(self) -> float:
        pass
