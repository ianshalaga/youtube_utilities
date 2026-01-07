from pathlib import Path
from abc import ABC, abstractmethod

from domain.media.video.video_signature import VideoSignature
from domain.media.video.video_encoding import VideoEncodingDescriptor


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
    """
    Contrato para proveedores de metadatos multimedia.

    Un MediaProbeProvider es responsable de obtener información
    técnica sobre archivos multimedia a partir de una fuente
    externa (ffprobe, mediainfo, etc.).

    No mantiene estado asociado a un archivo concreto.
    """

    @abstractmethod
    def duration(self, path: Path) -> float:
        """
        Devuelve la duración total del archivo multimedia
        expresada en segundos.
        """
        pass

    @abstractmethod
    def video_signature(self, path: Path) -> VideoSignature:
        """
        Devuelve la firma técnica del archivo de video.
        """
        pass

    @abstractmethod
    def video_encoding(self, path: Path) -> VideoEncodingDescriptor:
        pass
