"""
CLI principal del proyecto YouTube Utilities.

Este módulo expone los distintos casos de uso del sistema
mediante comandos de consola.

Ejemplos:

    python app.py video_music
    python app.py video_joiner
    python app.py video_converter
    python app.py create_db
    python app.py load_legacy
    python app.py ranking

La lógica de negocio permanece en:

    applications/

Este módulo solamente coordina la ejecución.
"""

from pathlib import Path
import argparse

# CORE
from core.config_manager import ConfigManager

# APPLICATIONS
from applications.video_music.processor import VideoMusicProcessor
from applications.video_joiner.processor import VideoJoinerProcessor
from applications.ranking_system.create_db import create_db
from applications.ranking_system.loaders.load_legacy import (
    run as run_load_legacy
)
from applications.ranking_system.queries.builder import (
    RankingQueryBuilder
)

# SERVICES
from services.system.process_runner import ProcessRunner
from services.media.video.converter import VideoConverter
from services.media.video.mkvmerge_runner import MKVMergeRunner
from services.media.audio.converter import AudioConverter
from services.media.ffprobe_provider import FFProbeProvider
from services.ranking.storage.session import SessionLocal


config = ConfigManager()


def run_video_music() -> None:
    """
    Genera vídeos musicales utilizando una plantilla de vídeo
    y múltiples pistas de audio.
    """

    process_runner = ProcessRunner()

    mkvmerge_runner = MKVMergeRunner(process_runner)
    audio_converter = AudioConverter(process_runner)
    ffprobe_provider = FFProbeProvider(process_runner)

    processor = VideoMusicProcessor(
        mkvmerge_runner=mkvmerge_runner,
        audio_converter=audio_converter,
        ffprobe_provider=ffprobe_provider
    )

    audios_dir = config.video_music_default_audios_dir

    processor.process(
        video_path=Path(config.video_music_default_video_path),
        audios_dir=Path(audios_dir),
        output_dir=Path(audios_dir)
        / Path(config.video_music_default_output_dir)
    )


def run_video_joiner() -> None:
    """
    Une múltiples vídeos en una compilación única.
    """

    process_runner = ProcessRunner()

    mkvmerge_runner = MKVMergeRunner(process_runner)
    ffprobe_provider = FFProbeProvider(process_runner)

    processor = VideoJoinerProcessor(
        mkvmerge_runner=mkvmerge_runner,
        ffprobe_provider=ffprobe_provider
    )

    videos_dir = Path(config.video_joiner_default_videos_dir)

    output_dir = (
        videos_dir
        / Path(config.video_joiner_default_output_dir)
    )

    end_screens_dir = (
        Path(config.video_joiner_default_end_screens_dir)
        if config.video_joiner_default_end_screens_dir
        else None
    )

    processor.process(
        videos_dir=videos_dir,
        output_dir=output_dir,
        base_name=config.video_joiner_default_video_name,
        target_duration=config.video_joiner_default_target_duration,
        end_screens_dir=end_screens_dir,
        random_end_screen=config.video_joiner_default_random_end_screen,
        timestamps_prefix=config.video_joiner_default_timestamps_prefix,
        timestamps_secuence=config.video_joiner_default_timestamps_secuence,
        extra_description=config.video_joiner_default_extra_description
    )


def run_video_converter() -> None:
    """
    Convierte vídeos utilizando una referencia de codificación.
    """

    probe_provider = FFProbeProvider()

    converter = VideoConverter(
        probe_provider=probe_provider
    )

    converter.convert(
        src=Path(config.video_converter_src),
        dst_dir=Path(config.video_converter_dst_dir),
        output_format=config.video_converter_output_format,
        reference_video=Path(
            config.video_converter_reference_video
        )
    )


def run_create_db() -> None:
    """
    Crea la estructura de base de datos del sistema ranking.
    """

    create_db()


def run_load_legacy() -> None:
    """
    Importa datos históricos desde el CSV legado.
    """

    csv_path = Path(
        "F:/DESCARGAS/SSLEdb - SSLT.csv"
    )

    run_load_legacy(csv_path=csv_path)


def run_ranking() -> None:
    """
    Ejecuta consultas del sistema de ranking.
    """

    session = SessionLocal()

    query = RankingQueryBuilder(
        session=session
    ).build(
        filters=config.ranking_filters
    )

    print(query)


def build_parser() -> argparse.ArgumentParser:
    """
    Construye el parser principal del CLI.
    """

    parser = argparse.ArgumentParser(
        prog="youtube_utilities",
        description="Herramientas multimedia y ranking."
    )

    parser.add_argument(
        "command",
        choices=[
            "video_music",
            "video_joiner",
            "video_converter",
            "create_db",
            "load_legacy",
            "ranking"
        ]
    )

    return parser


def main() -> None:
    """
    Punto de entrada principal del CLI.
    """

    parser = build_parser()

    args = parser.parse_args()

    commands = {
        "video_music": run_video_music,
        "video_joiner": run_video_joiner,
        "video_converter": run_video_converter,
        "create_db": run_create_db,
        "load_legacy": run_load_legacy,
        "ranking": run_ranking,
    }

    commands[args.command]()


if __name__ == "__main__":
    main()
