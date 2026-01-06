from pathlib import Path
from typing import Iterable

from domain.media.base import MediaProbeProvider
from domain.media.video.video_signature import VideoSignature


class VideoCompatibilityError(Exception):
    """
    Error lanzado cuando uno o más videos no son compatibles
    entre sí desde el punto de vista técnico.
    """
    pass


class VideoCompatibilityValidator:
    """
    Servicio encargado de validar la compatibilidad técnica
    entre archivos de video.

    La compatibilidad se determina comparando la firma técnica
    (VideoSignature) de cada archivo contra una referencia.

    Este servicio:
    - No ejecuta herramientas externas
    - No parsea metadatos
    - No contiene lógica de infraestructura
    """

    def __init__(self, probe: MediaProbeProvider):
        """
        Inicializa el validador con un proveedor de metadatos.

        Args:
            probe:
                Proveedor de metadatos multimedia.
        """
        self._probe = probe

    def validate(self, videos: Iterable[Path]) -> None:
        """
        Valida que todos los videos proporcionados sean
        técnicamente compatibles entre sí.

        La validación falla si alguna firma difiere de la
        firma de referencia.

        Args:
            videos:
                Iterable de rutas a archivos de video.

        Raises:
            VideoCompatibilityError:
                Si se detecta incompatibilidad entre los videos.
            ValueError:
                Si no se proporciona ningún video.
        """
        videos = list(videos)

        if not videos:
            raise ValueError("No videos provided for compatibility validation")

        reference_path = videos[0]
        reference_signature = self._signature(reference_path)

        for path in videos[1:]:
            signature = self._signature(path)
            if signature != reference_signature:
                raise VideoCompatibilityError(
                    self._build_error_message(
                        reference_path,
                        reference_signature,
                        path,
                        signature,
                    )
                )

    # ───────────────────────────────
    # Helpers privados
    # ───────────────────────────────

    def _signature(self, path: Path) -> VideoSignature:
        """
        Obtiene la firma técnica de un video.

        Args:
            path:
                Ruta del archivo de video.

        Returns:
            VideoSignature:
                Firma técnica del video.
        """
        return self._probe.video_signature(path)

    @staticmethod
    def _build_error_message(
        ref_path: Path,
        ref_sig: VideoSignature,
        path: Path,
        sig: VideoSignature,
    ) -> str:
        """
        Construye un mensaje de error descriptivo indicando
        qué video no es compatible con la referencia.

        Returns:
            str:
                Mensaje de error legible.
        """
        return (
            "Incompatible video detected:\n"
            f"- Reference: {ref_path}\n"
            f"  Signature: {ref_sig}\n"
            f"- Candidate: {path}\n"
            f"  Signature: {sig}"
        )
