import json
from pathlib import Path

from services.ranking.config.filters import (
    RankingFilters, ScopeFilters, DuelFilters,
    ParticipantFilters, BattleFilters, PlayerFilters
)


class ConfigManager:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    CONFIG_FILE = PROJECT_ROOT / "config.json"

    def __init__(self):
        if not self.CONFIG_FILE.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo de configuración: "
                f"{self.CONFIG_FILE}"
            )

        with self.CONFIG_FILE.open("r", encoding="utf-8") as f:
            self._config = json.load(f)

    def save(self):
        self.CONFIG_FILE.write_text(
            json.dumps(self._config, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    # ───────────────────────────────
    # PATHS @@@@
    # ───────────────────────────────
    @property
    def paths_mkvmerge(self) -> dict:
        return self._config["paths"]["mkvmerge"]

    @property
    def paths_ffmpeg(self) -> dict:
        return self._config["paths"]["ffmpeg"]

    @property
    def paths_probe(self) -> dict:
        return self._config["paths"]["probe"]

    # ───────────────────────────────
    # AUDIO @@@@
    # ───────────────────────────────
    @property
    def audio_target_codec(self) -> str:
        return self._config["audio"]["target_codec"]

    @property
    def audio_target_container(self) -> str:
        return self._config["audio"]["target_container"]

    @property
    def audio_target_bitrate(self) -> str:
        return self._config["audio"]["target_bitrate"]

    @property
    def audio_target_samplerate(self) -> int:
        return self._config["audio"]["target_samplerate"]

    @property
    def audio_lufs_target(self) -> int:
        return self._config["audio"]["lufs_target"]

    @property
    def audio_true_peak(self) -> int:
        return self._config["audio"]["true_peak"]

    @property
    def audio_lra(self) -> int:
        return self._config["audio"]["lra"]

    @property
    def audio_supported_extensions(self) -> list:
        return self._config["audio"]["supported_extensions"]

    # ───────────────────────────────
    # VIDEO @@@@
    # ───────────────────────────────
    @property
    def video_supported_extensions(self) -> list:
        return self._config["video"]["supported_extensions"]

    # ───────────────────────────────
    # APPS @@@@
    # ───────────────────────────────

    # ───────────────────────────────
    # VIDEO MUSIC @@@@
    # ───────────────────────────────
    @property
    def video_music_max_items_per_dir(self) -> int:
        return self._config["apps"]["video_music"]["max_items_per_dir"]

    @property
    def video_music_default_video_path(self) -> str:
        return self._config["apps"]["video_music"]["default_video_path"]

    @property
    def video_music_default_audios_dir(self) -> str:
        return self._config["apps"]["video_music"]["default_audios_dir"]

    @property
    def video_music_default_output_dir(self) -> str:
        return self._config["apps"]["video_music"]["default_output_dir"]

    # ───────────────────────────────
    # VIDEO JOINER @@@@
    # ───────────────────────────────

    @property
    def video_joiner_max_items_per_dir(self) -> int:
        return self._config["apps"]["video_joiner"]["max_items_per_dir"]

    @property
    def video_joiner_default_videos_dir(self) -> str:
        return self._config["apps"]["video_joiner"]["default_videos_dir"]

    @property
    def video_joiner_default_output_dir(self) -> str:
        return self._config["apps"]["video_joiner"]["default_output_dir"]

    @property
    def video_joiner_default_video_name(self) -> str:
        return self._config["apps"]["video_joiner"]["default_video_name"]

    @property
    def video_joiner_default_target_duration(self) -> int:
        return self._config["apps"]["video_joiner"]["default_target_duration"]

    @property
    def video_joiner_default_end_screens_dir(self) -> str:
        return self._config["apps"]["video_joiner"]["default_end_screens_dir"]

    @property
    def video_joiner_default_random_end_screen(self) -> bool:
        return self._config["apps"]["video_joiner"]["default_random_end_screen"]

    @property
    def video_joiner_default_timestamps_prefix(self) -> str:
        return self._config["apps"]["video_joiner"]["default_timestamps_prefix"]

    @property
    def video_joiner_default_extra_description(self) -> str:
        return self._config["apps"]["video_joiner"]["default_extra_description"]

    @property
    def video_joiner_default_timestamps_secuence(self) -> list:
        return self._config["apps"]["video_joiner"]["default_timestamps_secuence"]

    # ───────────────────────────────
    # VIDEO CONVERTER @@@@
    # ───────────────────────────────

    @property
    def video_formats(self) -> dict:
        return self._config["apps"]["video_converter"]["video_formats"]

    @property
    def video_converter_src(self) -> str:
        return self._config["apps"]["video_converter"]["src"]

    @property
    def video_converter_dst_dir(self) -> str:
        return self._config["apps"]["video_converter"]["dst_dir"]

    @property
    def video_converter_output_format(self) -> str:
        return self._config["apps"]["video_converter"]["output_format"]

    @property
    def video_converter_reference_video(self) -> str:
        return self._config["apps"]["video_converter"]["reference_video"]

    # ───────────────────────────────
    # RANKING SYSTEM  @@@@
    # ───────────────────────────────
    @property
    def ranking_entity(self) -> str:
        return self._config["apps"]["ranking_system"]["entity"]

    @property
    def ranking_filters(self) -> RankingFilters:
        raw = self._config["apps"]["ranking_system"]["filters"]

        return RankingFilters(
            scope=ScopeFilters(**raw["scope"]),
            duel=DuelFilters(**raw["duel"]),
            participant=ParticipantFilters(**raw["participant"]),
            battle=BattleFilters(**raw["battle"]),
            player=PlayerFilters(**raw["player"]),
        )

    @property
    def ranking_export_format(self) -> str:
        return self._config["apps"]["ranking_system"]["export"]["format"]

    @property
    def ranking_export_output(self) -> str:
        return self._config["apps"]["ranking_system"]["export"]["output"]
