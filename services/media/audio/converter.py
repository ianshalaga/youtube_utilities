"""
NOTAS DE IMPLEMENTACIÓN (uso personal)

- ffmpeg:
    - "-y": sobrescribe archivos de salida sin pedir confirmación.
    - "-vn": desactiva cualquier stream de video (audio only).
    - "-af loudnorm": aplica normalización por sonoridad según EBU R128.
        - I  (LUFS): sonoridad integrada objetivo.
        - TP (True Peak): pico máximo permitido.
        - LRA: rango dinámico objetivo.
- subprocess.run(..., check=True):
    - Lanza CalledProcessError si ffmpeg falla.
- Path / operador "/":
    - Permite componer rutas de forma portable.
- Archivos temporales:
    - El sufijo "_tmp" indica que el archivo debe eliminarse tras su uso.
"""

from pathlib import Path
import subprocess

from core.config_manager import ConfigManager
from services.system.process_runner import ProcessRunner


class AudioConverter:
    """
    Convierte archivos de audio a un formato objetivo definido por configuración.

    Responsabilidades:
    - Ejecutar ffmpeg como herramienta externa
    - Normalizar la sonoridad del audio
    - Recodificar a un codec, bitrate y sample rate específicos
    - Generar un archivo temporal listo para muxeo posterior

    Esta clase no valida contenido multimedia ni maneja limpieza
    del archivo temporal; esas responsabilidades pertenecen al caller.
    """

    def __init__(self, process_runner: ProcessRunner):
        """
        Inicializa el convertidor de audio.
        """
        self._config = ConfigManager()
        self._runner = process_runner

    def convert(self, src: Path, dst_dir: Path) -> Path:
        """
        Convierte un archivo de audio a un formato temporal normalizado.

        El archivo resultante:
        - Usa el codec, bitrate y sample rate definidos en configuración
        - Aplica normalización por sonoridad
        - Se escribe en el directorio destino con sufijo "_tmp"

        Args:
            src:
                Ruta del archivo de audio original.
            dst_dir:
                Directorio donde se escribirá el archivo convertido.

        Returns:
            Path:
                Ruta del archivo de audio temporal generado.

        Raises:
            subprocess.CalledProcessError:
                Si ffmpeg falla durante la conversión.
        """
        dst_dir.mkdir(exist_ok=True)

        # Archivo temporal: mismo nombre base, distinto contenedor
        dst_path = dst_dir / \
            f"{src.stem}_tmp.{self._config.audio_target_container}"

        cmd = [
            self._config.paths_ffmpeg,
            "-y",                      # sobrescritura forzada
            "-i", str(src),            # archivo de entrada
            "-vn",                     # elimina cualquier stream de video
            "-af", (
                f"loudnorm="
                f"I={self._config.audio_lufs_target}:"
                f"TP={self._config.audio_true_peak}:"
                f"LRA={self._config.audio_lra}"
            ),
            "-c:a", self._config.audio_target_codec,
            "-b:a", self._config.audio_target_bitrate,
            "-ar", str(self._config.audio_target_samplerate),
            "-ac", "2",
            str(dst_path),
        ]

        self._runner.run(cmd)

        return dst_path
