from abc import ABC, abstractmethod
from pathlib import Path

from domain.media.video.video_signature import VideoSignature
from domain.media.video.video_encoding import VideoEncodingDescriptor


class MediaProvider(ABC):
    """
    Contrato para proveedores de metadatos multimedia.

    Un MediaProvider es responsable de obtener información
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
