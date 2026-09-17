"""
CLI principal del proyecto YouTube Utilities.

Este módulo expone los distintos casos de uso del sistema
mediante comandos de consola.

La lógica de negocio permanece en:

    applications/

Este módulo solamente coordina la ejecución.
"""

import argparse
from pathlib import Path

# CORE
from core.config_manager import ConfigManager

# APPLICATIONS
from applications.video_music.processor import VideoMusicProcessor
from applications.video_joiner.processor import VideoJoinerProcessor
from applications.ranking_system.create_db import create_db
from applications.ranking_system.loaders.load_legacy import (
    run as load_legacy,
)
from applications.ranking_system.queries.builder import RankingQueryBuilder
from applications.youtube_video_manager.processor import (
    YouTubeVideoManagerProcessor,
)

# SERVICES
from services.media.audio.converter import AudioConverter
from services.media.ffprobe_provider import FFProbeProvider
from services.media.video.converter import VideoConverter
from services.media.video.mkvmerge_runner import MKVMergeRunner
from services.ranking.storage.session import SessionLocal
from services.system.process_runner import ProcessRunner
from services.youtube.album_builder import AlbumBuilder
from services.youtube.album_manifest.yaml_reader import YamlReader
from services.youtube.api.client import YouTubeClient
from services.youtube.api.methods import YouTubeMethods
from services.youtube.operations_builder import OperationsBuilder
from services.youtube.planner import Planner
from services.youtube.storage.mappers.job_mapper import JobMapper
from services.youtube.storage.repository import YouTubeJobRepository
from services.youtube.storage.session import SessionLocal as YouTubeSessionLocal
from services.youtube.updater import Updater
from services.youtube.youtube_discovery import YouTubeDiscovery


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
        ffprobe_provider=ffprobe_provider,
    )

    audios_dir = config.video_music_default_audios_dir

    processor.process(
        video_path=Path(config.video_music_default_video_path),
        audios_dir=Path(audios_dir),
        output_dir=Path(audios_dir)
        / Path(config.video_music_default_output_dir),
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
        ffprobe_provider=ffprobe_provider,
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
        extra_description=config.video_joiner_default_extra_description,
    )


def run_video_converter() -> None:
    """
    Convierte vídeos utilizando una referencia de codificación.
    """

    probe_provider = FFProbeProvider()

    converter = VideoConverter(
        probe_provider=probe_provider,
    )

    converter.convert(
        src=Path(config.video_converter_src),
        dst_dir=Path(config.video_converter_dst_dir),
        output_format=config.video_converter_output_format,
        reference_video=Path(
            config.video_converter_reference_video,
        ),
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
        "F:/DESCARGAS/SSLEdb - SSLT.csv",
    )

    load_legacy(csv_path=csv_path)


def run_ranking() -> None:
    """
    Ejecuta consultas del sistema de ranking.
    """

    session = SessionLocal()

    query = RankingQueryBuilder(
        session=session,
    ).build(
        filters=config.ranking_filters,
    )

    print(query)


def _ask_youtube_failure_action() -> str:
    while True:
        action = input(
            "The previous YouTube job failed. "
            "Choose [retry/discard]: "
        ).strip().lower()

        if action in {"retry", "discard"}:
            return action

        print("Invalid action. Please enter 'retry' or 'discard'.")


def run_youtube_video_manager() -> None:
    """
    Ejecuta el caso de uso de gestión de vídeos de YouTube.
    """

    # -------------------------------------------------------------------------
    # YouTube API
    # -------------------------------------------------------------------------

    youtube_client = YouTubeClient(
        client_secrets_path=Path(
            config.youtube_video_manager_client_secrets_path,
        ),
        token_path=Path(
            config.youtube_video_manager_token_path,
        ),
    )

    youtube_methods = YouTubeMethods(
        youtube_client,
    )

    youtube_discovery = YouTubeDiscovery(
        methods=youtube_methods,
    )

    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------

    youtube_session = YouTubeSessionLocal()

    try:
        job_mapper = JobMapper()

        job_repository = YouTubeJobRepository(
            session=youtube_session,
            mapper=job_mapper,
        )

        # ---------------------------------------------------------------------
        # Album / planning
        # ---------------------------------------------------------------------

        manifest_reader = YamlReader()
        album_builder = AlbumBuilder()

        operations_builder = OperationsBuilder()
        planner = Planner(
            operations_builder=operations_builder,
        )

        # ---------------------------------------------------------------------
        # Execution
        # ---------------------------------------------------------------------

        updater = Updater(
            youtube_methods=youtube_methods,
            job_repository=job_repository,
            max_attempts=config.youtube_video_manager_max_attempts,
        )

        # ---------------------------------------------------------------------
        # Application
        # ---------------------------------------------------------------------

        processor = YouTubeVideoManagerProcessor(
            manifest_reader=manifest_reader,
            youtube_discovery=youtube_discovery,
            album_builder=album_builder,
            planner=planner,
            updater=updater,
            job_repository=job_repository,
            failure_action=_ask_youtube_failure_action,
        )

        processor.process(
            Path(
                config.youtube_video_manager_album_manifest_path,
            ),
        )
    finally:
        youtube_session.close()


def build_parser() -> argparse.ArgumentParser:
    """
    Construye el parser principal del CLI.
    """

    parser = argparse.ArgumentParser(
        prog="youtube_utilities",
        description="Herramientas multimedia y ranking.",
    )

    parser.add_argument(
        "command",
        choices=[
            "video_music",
            "video_joiner",
            "video_converter",
            "create_db",
            "load_legacy",
            "ranking",
            "midi_mapper",
            "youtube_video_manager",
        ],
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
        "youtube_video_manager": run_youtube_video_manager,
    }

    commands[args.command]()


if __name__ == "__main__":
    main()