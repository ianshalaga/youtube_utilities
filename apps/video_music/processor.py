"""
NOTAS DE IMPLEMENTACIÓN (uso personal)

- Path.iterdir(): devuelve un iterador de Path, no una lista.
- sorted(Path): ordena lexicográficamente; funciona correctamente
  cuando los nombres de archivo comienzan con 01, 02, 03, etc.
- // (floor division): división entera, devuelve el cociente truncado.
  Se usa para agrupar elementos en bloques de tamaño fijo.
- enumerate(iterable): devuelve pares (índice, elemento).
- f"{value:0Nd}": formateo con padding de ceros a la izquierda.
- raise ValueError: excepción adecuada para errores de uso/entrada.
- or : devuelve el primer valor truthy
"""

from pathlib import Path
from math import ceil

from core.config_manager import ConfigManager
from domain.media.base import MediaProbeProvider
from domain.media.audio import Audio
from domain.media.video import Video
from services.media.video.mkvmerge_runner import MKVMergeRunner
from services.media.probe_provider import FFprobeMediaProbeProvider


class VideoMusicProcessor:
    """
    Orquesta la generación de videos musicales a partir de un video base
    y un conjunto de archivos de audio.

    Responsabilidades:
    - Mantener el orden original de las pistas
    - Limitar la cantidad de videos por directorio de salida
    - Crear subdirectorios numerados cuando sea necesario
    - Delegar la lógica de corte y muxeo a MKVMergeRunner

    Esta clase no realiza procesamiento multimedia directo; actúa
    únicamente como coordinador del flujo.
    """

    def __init__(
        self,
        max_items_per_dir: int | None = None,
        probe_provider: MediaProbeProvider | None = None
    ):
        """
        Inicializa el processor.

        Args:
            max_items_per_dir:
                Cantidad máxima de elementos por subdirectorio.
                Si no se especifica, se obtiene desde la configuración.
            probe_provider:
                Proveedor para obtener metadatos multimedia (duración).
                Permite inyección para tests o implementaciones futuras.
        """
        self._config = ConfigManager()
        self._mkvmerge = MKVMergeRunner()

        # Inyección explícita del provider para evitar dependencias ocultas
        self._probe_provider = probe_provider or FFprobeMediaProbeProvider()

        # Permite override explícito o fallback a configuración persistente
        self._max_items_per_dir = (
            max_items_per_dir
            if max_items_per_dir is not None
            else self._config.video_music_max_items_per_dir
        )

    def process(
        self,
        video_path: Path,
        audios_dir: Path,
        output_dir: Path
    ) -> None:
        """
        Procesa un directorio de canciones y genera un video por cada pista.

        Dependiendo de la cantidad de canciones y del límite configurado,
        los resultados se escribirán directamente en el directorio de salida
        o bien se dividirán en subdirectorios numerados.

        Args:
            video_path:
                Ruta al archivo de video base.
            songs_dir:
                Directorio que contiene los archivos de audio a procesar.
            output_dir:
                Directorio donde se escribirán los videos resultantes.

        Raises:
            ValueError:
                Si no se encuentran archivos de audio en el directorio.
        """

        # Se asume que el directorio contiene solo audio válido;
        # esta validación es preventiva y de bajo coste.
        audio_files = sorted(
            p for p in audios_dir.iterdir()
            if p.is_file() and p.suffix.lower().lstrip(".") in self._config.audio_supported_extensions
        )

        if not audio_files:
            raise ValueError("No se encontraron archivos de audio.")

        output_dir.mkdir(parents=True, exist_ok=True)

        total_songs = len(audio_files)

        # ───────────────────────────────
        # MODO SIN SUBDIRECTORIOS
        # ───────────────────────────────
        if total_songs <= self._max_items_per_dir:
            for audio_path in audio_files:
                self._mkvmerge.cut_video(
                    video=video_path,
                    audio=audio_path,
                    output_dir=output_dir
                )
            return

        # ───────────────────────────────
        # MODO CON SUBDIRECTORIOS
        # ───────────────────────────────
        total_subdirs = ceil(total_songs / self._max_items_per_dir)

        # Determina el padding dinámico (1 → 1..9, 01 → 10..99, etc.)
        padding = len(str(total_subdirs))

        for index, audio_path in enumerate(audio_files):
            subdir = self._get_subdir_path(
                file_index=index,
                padding=padding,
                output_dir=output_dir
            )
            subdir.mkdir(exist_ok=True)

            self._mkvmerge.cut_video(
                video=video_path,
                audio=audio_path,
                output_dir=subdir
            )

    def _get_subdir_path(
        self,
        file_index: int,
        padding: int,
        output_dir: Path
    ) -> Path:
        """
        Calcula el subdirectorio de salida correspondiente a un archivo.

        El cálculo se basa en bloques de tamaño `max_items_per_dir`,
        preservando el orden global de las pistas.

        Args:
            file_index:
                Índice del archivo dentro de la lista total.
            padding:
                Cantidad de dígitos a usar en el nombre del directorio.
            output_dir:
                Directorio raíz de salida.

        Returns:
            Ruta completa al subdirectorio correspondiente.
        """
        # División entera para agrupar índices en bloques fijos
        subdir_number = (file_index // self._max_items_per_dir) + 1

        subdir_name = f"{subdir_number:0{padding}d}"
        return output_dir / subdir_name
