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

from rich.console import Console

# CORE
from core.config_manager import ConfigManager
from domain.youtube.job import JobStatus

# APPLICATIONS
from applications.video_music.processor import VideoMusicProcessor
from applications.video_music.input import VideoMusicInput
from applications.video_joiner.processor import VideoJoinerProcessor
from applications.video_joiner.console import VideoJoinerConsole
from applications.ranking_system.create_db import create_db
from applications.ranking_system.loaders.load_legacy import (
    run as load_legacy,
)
from applications.ranking_system.queries.builder import RankingQueryBuilder

# SERVICES
from services.media.audio.converter import AudioConverter
from services.media.ffprobe_provider import FFProbeProvider
from services.media.video.converter import VideoConverter
from services.media.video.mkvmerge_runner import MKVMergeRunner
from services.ranking.storage.session import SessionLocal
from services.system.process_runner import ProcessRunner
from services.youtube.console import YouTubeConsole
from services.youtube.storage.session import SessionLocal as YouTubeSessionLocal

# COMPOSITION
from composition.video_music import VideoMusicProcessorFactory
from composition.youtube_video_manager import (
    YouTubeVideoManagerProcessorFactory,
)

# INTERFACES
from interfaces.cli.presenters.video_music_result_presenter import (
    VideoMusicResultPresenter,
)
from interfaces.cli.builders.video_music_input_builder import (
    build_video_music_input,
)
from interfaces.cli.menus.youtube_video_manager_menu import (
    MenuAction,
    YouTubeVideoManagerMenu,
)
from interfaces.cli.menus.youtube_video_manager_prompts import (
    YouTubeVideoManagerPrompts,
)


def run_video_music(config: ConfigManager) -> None:
    input_data = build_video_music_input(config)

    processor = VideoMusicProcessorFactory.create_processor(config)
    result = processor.process(input_data)

    presenter = VideoMusicResultPresenter()
    presenter.display(result)


def run_video_joiner(config: ConfigManager) -> None:
    """
    Une múltiples vídeos en una compilación única.
    """

    process_runner = ProcessRunner()

    mkvmerge_runner = MKVMergeRunner(process_runner)
    ffprobe_provider = FFProbeProvider(process_runner)

    processor = VideoJoinerProcessor(
        mkvmerge_runner=mkvmerge_runner,
        ffprobe_provider=ffprobe_provider,
        console=VideoJoinerConsole(),
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


def run_video_converter(config: ConfigManager) -> None:
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


def run_ranking(config: ConfigManager) -> None:
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


def run_youtube_video_manager(config: ConfigManager) -> None:
    """
    Ejecuta el caso de uso de gestión de vídeos de YouTube.
    """

    youtube_session = YouTubeSessionLocal()

    try:
        terminal = Console()
        console = YouTubeConsole(terminal)
        processor = YouTubeVideoManagerProcessorFactory.create_processor(
            config=config,
            session=youtube_session,
            console=console,
        )

        manifest_path = Path(
            config.youtube_video_manager_album_manifest_path,
        )
        menu = YouTubeVideoManagerMenu(console=terminal)
        prompts = YouTubeVideoManagerPrompts(console=terminal)

        try:
            while True:
                selection = menu.select(processor.list_jobs())
                if selection is None:
                    return

                if selection.action is MenuAction.CREATE_JOB:
                    processor.create_and_save_job(manifest_path)
                    continue

                if selection.job_id is None:
                    continue

                job = processor.get_job(selection.job_id)
                if job is None:
                    console.job_not_found(selection.job_id)
                    continue

                try:
                    if job.status is JobStatus.CREATED:
                        publication = prompts.ask_created_job_publication(job)
                        if publication is not None:
                            processor.start_created_job(job, publication)
                    elif job.status is JobStatus.PENDING:
                        processor.continue_pending_job(job)
                    elif job.status is JobStatus.FAILED:
                        action = prompts.ask_failed_job_action()
                        if action == "retry":
                            processor.retry_failed_job(job)
                        elif action == "delete":
                            processor.delete_job(job)
                    elif job.status is JobStatus.RUNNING:
                        console.running_job_recovery_warning(job)
                        action = prompts.ask_running_job_action()
                        if action == "resume":
                            processor.recover_running_job(job)
                        elif action == "delete":
                            processor.delete_job(job)
                except Exception as error:
                    console.job_action_failed(error)
        except KeyboardInterrupt:
            return
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
    config = ConfigManager()

    parser = build_parser()

    args = parser.parse_args()

    commands = {
        "video_music": lambda: run_video_music(config),
        "video_joiner": lambda: run_video_joiner(config),
        "video_converter": lambda: run_video_converter(config),
        "create_db": run_create_db,
        "load_legacy": run_load_legacy,
        "ranking": lambda: run_ranking(config),
        "youtube_video_manager": lambda: run_youtube_video_manager(config),
    }

    commands[args.command]()


if __name__ == "__main__":
    main()
