"""
NOTAS DE IMPLEMENTACIÓN (uso personal)

- mkvmerge:
    - Cada archivo agregado aporta todas sus pistas por defecto.
    - Las opciones como --no-audio y --no-subtitles afectan solo
      al archivo que las precede.
    - --split parts:HH:MM:SS-HH:MM:SS genera múltiples segmentos.
- subprocess.run(..., check=True):
    - Lanza CalledProcessError si el comando falla.
- try / finally:
    - Se usa aquí exclusivamente para garantizar limpieza
      del archivo de audio temporal.
- Path.glob():
    - Devuelve resultados no ordenados; se ordenan explícitamente.
"""

from pathlib import Path
import subprocess

from core.config_manager import ConfigManager
from core.time_utils import seconds_to_hhmmss_ms
from domain.media.audio import Audio
from services.media.audio.converter import AudioConverter
from services.media.probe_provider import FFprobeMediaProbeProvider


class MKVMergeRunner:
    """
    Ejecuta mkvmerge para generar un video final a partir de:
    - un video base
    - una pista de audio convertida previamente

    Responsabilidades:
    - Convertir el audio a un formato compatible
    - Calcular la duración efectiva del audio convertido
    - Cortar el video base a dicha duración
    - Eliminar pistas de audio y subtítulos del video original
    - Limpiar archivos temporales y segmentos sobrantes

    Esta clase actúa como una capa de infraestructura y
    encapsula el uso de herramientas externas (mkvmerge, ffmpeg).
    """

    def __init__(self):
        self._config = ConfigManager()
        self._audio_converter = AudioConverter()
        self._media_probe_provider = FFprobeMediaProbeProvider()

    def cut_video(self, video_path: Path, audio_path: Path, output_dir: Path):
        """
        Genera un video final combinando un video base con una pista de audio.

        El proceso consiste en:
        1. Convertir el audio a un formato temporal compatible
        2. Obtener la duración exacta del audio convertido
        3. Ejecutar mkvmerge para cortar el video base y muxear el audio
        4. Eliminar segmentos extra generados por mkvmerge
        5. Limpiar archivos temporales

        Args:
            video_path:
                Ruta del video base.
            audio_path:
                Ruta de la pista de audio original.
            output_dir:
                Directorio donde se escribirá el archivo final.

        Raises:
            FileNotFoundError:
                Si el archivo de video o audio no existe.
            subprocess.CalledProcessError:
                Si mkvmerge o ffmpeg fallan durante la ejecución.
        """
        if not video_path.exists():
            raise FileNotFoundError(video_path)

        if not audio_path.exists():
            raise FileNotFoundError(audio_path)

        output_dir.mkdir(exist_ok=True, parents=True)

        # Conversión del audio a un formato temporal
        tmp_audio_path = self._audio_converter.convert(
            src=audio_path,
            dst_dir=output_dir
        )

        try:
            # Se calcula la duración usando el audio convertido,
            # no el original, para máxima precisión.
            duration_seconds = self._media_probe_provider.duration(
                tmp_audio_path)

            duration = seconds_to_hhmmss_ms(duration_seconds)

            output_path = output_dir / f"{audio_path.stem}.mkv"

            cmd = [
                self._config.paths_mkvmerge,
                "-o", str(output_path),
                "--split", f"parts:00:00:00-{duration}",
                "--no-audio",
                "--no-subtitles",
                str(video_path),
                "--audio-tracks", "0",
                str(tmp_audio_path),
            ]

            subprocess.run(cmd, check=True)

            # mkvmerge genera múltiples archivos; se conserva solo el primero
            self._cleanup_segments(output_dir, audio_path.stem)

        finally:
            # Limpieza garantizada del archivo temporal, incluso si falla mkvmerge
            if tmp_audio_path.exists():
                tmp_audio_path.unlink()

    def _cleanup_segments(self, output_dir: Path, base_name: str):
        """
        Elimina segmentos sobrantes generados por mkvmerge y
        renombra el archivo principal.
        No maneja colisiones de nombres pero no deberían darse.

        Args:
            output_dir:
                Directorio donde se encuentran los segmentos generados.
            base_name:
                Nombre base del archivo sin sufijos de segmentación.
        """
        files = sorted(output_dir.glob(f"{base_name}-*.mkv"))
        if not files:
            return

        main_file = files[0]
        final_name = output_dir / f"{base_name}.mkv"
        main_file.rename(final_name)

        for f in files[1:]:
            f.unlink()
