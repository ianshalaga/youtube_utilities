from pathlib import Path

# CORE
from core.config_manager import ConfigManager  # Fuente de obtención de datos

# APPS
from apps.video_music.processor import VideoMusicProcessor
from apps.video_joiner.processor import VideoJoinerProcessor
from apps.ranking_system.create_db import create_db
from apps.ranking_system.loaders.load_legacy import run as run_load_legacy
# from apps.ranking_system.processor import run_ranking
from apps.ranking_system.queries.builder import RankingQueryBuilder

# SERVICES
from services.system.process_runner import ProcessRunner
from services.media.video.converter import VideoConverter
from services.media.video.mkvmerge_runner import MKVMergeRunner
from services.media.audio.converter import AudioConverter
from services.media.ffprobe_provider import FFProbeProvider
from services.ranking.storage.session import SessionLocal


config = ConfigManager()

video_music = False
video_joiner = False
video_converter = False
db = False
load_legacy = True
ranking_system = False


csv_legacy_path = Path("F:/DESCARGAS/SSLEdb - SSLT.csv")


# ───────────────────────────────
# VIDEO MUSIC @@@@
# ───────────────────────────────

if video_music:
    process_runner = ProcessRunner()

    mkvmerge_runner = MKVMergeRunner(process_runner)
    audio_converter = AudioConverter(process_runner)
    ffprobe_provider = FFProbeProvider(process_runner)

    video_music_processor = VideoMusicProcessor(
        mkvmerge_runner=mkvmerge_runner,
        audio_converter=audio_converter,
        ffprobe_provider=ffprobe_provider
    )

    audios_dir = config.video_music_default_audios_dir

    video_music_processor.process(
        video_path=Path(config.video_music_default_video_path),
        audios_dir=Path(audios_dir),
        output_dir=Path(audios_dir) /
        Path(config.video_music_default_output_dir)
    )


# ───────────────────────────────
# VIDEO JOINER @@@@
# ───────────────────────────────

if video_joiner:
    process_runner = ProcessRunner()

    mkvmerge_runner = MKVMergeRunner(process_runner)
    ffprobe_provider = FFProbeProvider(process_runner)

    video_joiner_processor = VideoJoinerProcessor(
        mkvmerge_runner=mkvmerge_runner,
        ffprobe_provider=ffprobe_provider
    )

    videos_dir = Path(config.video_joiner_default_videos_dir)
    output_dir = videos_dir / Path(config.video_joiner_default_output_dir)
    end_screens_dir = Path(
        config.video_joiner_default_end_screens_dir) if config.video_joiner_default_end_screens_dir else None

    video_joiner_processor.process(
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


# ───────────────────────────────
# VIDEO CONVERTER @@@@
# ───────────────────────────────

if video_converter:
    probe_provider = FFProbeProvider()
    video_converter = VideoConverter(probe_provider=probe_provider)

    src = Path(config.video_converter_src)
    dst_dir = Path(config.video_converter_dst_dir)
    output_format = config.video_converter_output_format
    reference_video = Path(config.video_converter_reference_video)

    video_converter.convert(
        src=src,
        dst_dir=dst_dir,
        output_format=output_format,
        reference_video=reference_video
    )


# ───────────────────────────────
# RANKING SYSTEM @@@@
# ───────────────────────────────

if db:
    create_db()

if load_legacy:
    run_load_legacy(csv_path=csv_legacy_path)

if ranking_system:
    session = SessionLocal()

    filters = config.ranking_filters
    query = RankingQueryBuilder(session=session).build(filters=filters)

    # results = run_ranking(
    #     session=session,
    #     entity=config.ranking_entity,
    #     query=query,
    # )

    # export simple (luego se refina)
    # for _, stats in results.items():
    #     print(stats)
