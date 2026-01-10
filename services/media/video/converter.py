"""
NOTAS DE IMPLEMENTACIÓN (uso personal)

- ffmpeg:
    - "-y": sobrescribe archivos de salida sin confirmación
    - "-map 0:v:0": toma el primer stream de video
    - "-map 0:a:0?": toma audio si existe (opcional)
- El formato de salida puede:
    - Definirse explícitamente
    - Derivarse de un video de referencia
- ffprobe se usa indirectamente vía MediaProvider
- Esta clase NO valida compatibilidad semántica
"""

from pathlib import Path
import subprocess

from core.config_manager import ConfigManager
from services.media.media_provider import MediaProvider


class VideoConverter:
    """
    Convierte archivos de video a un formato objetivo.

    Responsabilidades:
    - Ejecutar ffmpeg
    - Convertir video y audio
    - Soportar formato explícito o derivado de un video de referencia

    No paraleliza ni valida compatibilidad avanzada.
    """

    def __init__(self, media_provider: MediaProvider):
        self._config = ConfigManager()
        self._media_provider = media_provider

    def convert(
        self,
        src: Path,
        dst_dir: Path,
        *,
        output_format: str | None = None,
        reference_video: Path | None = None
    ) -> Path:
        """
        Convierte un archivo de video.
        """
        if not src.exists():
            raise FileNotFoundError(src)

        if (output_format is None) == (reference_video is None):
            raise ValueError(
                "Debe especificarse output_format o reference_video (excluyentes)."
            )

        if reference_video is not None and not reference_video.exists():
            raise FileNotFoundError(reference_video)

        dst_dir.mkdir(parents=True, exist_ok=True)

        if reference_video is not None:
            format_params = self._extract_format(reference_video)
            container = reference_video.suffix.lstrip(".")
        else:
            format_params = self._get_format_from_config(output_format)
            container = output_format

        output_path = dst_dir / f"{src.stem}.{container}"

        cmd = [
            self._config.paths_ffmpeg,
            "-y",
            "-i", str(src),
            "-map", "0:v:0",
            "-map", "0:a:0?",
            *format_params,
            str(output_path),
        ]

        subprocess.run(cmd, check=True)

        return output_path

    # ───────────────────────────────
    # Formato explícito
    # ───────────────────────────────
    def _get_format_from_config(self, output_format: str) -> list[str]:
        if output_format not in self._config.video_formats:
            raise ValueError(f"Formato de video no soportado: {output_format}")

        fmt = self._config.video_formats[output_format]

        return [
            "-c:v", fmt["video_codec"],
            "-b:v", fmt["video_bitrate"],
            "-r", str(fmt["framerate"]),
            "-s", fmt["resolution"],
            "-pix_fmt", fmt.get("pixel_format", "yuv420p"),
            "-c:a", fmt["audio_codec"],
            "-b:a", fmt["audio_bitrate"],
            "-ar", str(fmt["audio_samplerate"]),
        ]

    # ───────────────────────────────
    # Formato desde video de referencia
    # ───────────────────────────────
    def _extract_format(self, reference_video: Path) -> list[str]:
        """
        Extrae parámetros técnicos de conversión a partir
        de un video de referencia.
        """
        encoding = self._media_provider.video_encoding(reference_video)

        params = [
            "-c:v", encoding.video_codec,
            "-pix_fmt", encoding.pixel_format,
            "-r", str(encoding.frame_rate),
            "-s", f"{encoding.width}x{encoding.height}",
        ]

        if encoding.video_bitrate:
            params += ["-b:v", encoding.video_bitrate]

        if encoding.audio_codec:
            params += ["-c:a", encoding.audio_codec]

            if encoding.audio_bitrate:
                params += ["-b:a", encoding.audio_bitrate]

            if encoding.sample_rate:
                params += ["-ar", str(encoding.sample_rate)]

            if encoding.channels:
                params += ["-ac", str(encoding.channels)]
        else:
            params.append("-an")

        return params
