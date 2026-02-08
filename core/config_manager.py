import json
from pathlib import Path


class ConfigManager:
    FILE = Path("config.json")

    def __init__(self):
        if not self.FILE.exists():
            raise FileNotFoundError("config.json no encontrado")
        self.data = json.loads(self.FILE.read_text(encoding="utf-8"))

    def save(self):
        self.FILE.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    # ───────────────────────────────
    # PATHS @@@@
    # ───────────────────────────────
    @property
    def paths_mkvmerge(self) -> dict:
        return self.data["paths"]["mkvmerge"]

    @property
    def paths_ffmpeg(self) -> dict:
        return self.data["paths"]["ffmpeg"]

    @property
    def paths_probe(self) -> dict:
        return self.data["paths"]["probe"]

    # ───────────────────────────────
    # AUDIO @@@@
    # ───────────────────────────────
    @property
    def audio_target_codec(self) -> str:
        return self.data["audio"]["target_codec"]

    @property
    def audio_target_container(self) -> str:
        return self.data["audio"]["target_container"]

    @property
    def audio_target_bitrate(self) -> str:
        return self.data["audio"]["target_bitrate"]

    @property
    def audio_target_samplerate(self) -> int:
        return self.data["audio"]["target_samplerate"]

    @property
    def audio_lufs_target(self) -> int:
        return self.data["audio"]["lufs_target"]

    @property
    def audio_true_peak(self) -> int:
        return self.data["audio"]["true_peak"]

    @property
    def audio_lra(self) -> int:
        return self.data["audio"]["lra"]

    @property
    def audio_supported_extensions(self) -> list:
        return self.data["audio"]["supported_extensions"]

    # ───────────────────────────────
    # VIDEO @@@@
    # ───────────────────────────────
    @property
    def video_supported_extensions(self) -> list:
        return self.data["video"]["supported_extensions"]

    # ───────────────────────────────
    # APPS @@@@
    # ───────────────────────────────

    # ───────────────────────────────
    # VIDEO MUSIC @@@@
    # ───────────────────────────────
    @property
    def video_music_max_items_per_dir(self) -> int:
        return self.data["apps"]["video_music"]["max_items_per_dir"]

    @property
    def video_music_default_video_path(self) -> str:
        return self.data["apps"]["video_music"]["default_video_path"]

    @property
    def video_music_default_audios_dir(self) -> str:
        return self.data["apps"]["video_music"]["default_audios_dir"]

    @property
    def video_music_default_output_dir(self) -> str:
        return self.data["apps"]["video_music"]["default_output_dir"]

    # ───────────────────────────────
    # VIDEO JOINER @@@@
    # ───────────────────────────────

    @property
    def video_joiner_max_items_per_dir(self) -> int:
        return self.data["apps"]["video_joiner"]["max_items_per_dir"]

    @property
    def video_joiner_default_videos_dir(self) -> str:
        return self.data["apps"]["video_joiner"]["default_videos_dir"]

    @property
    def video_joiner_default_output_dir(self) -> str:
        return self.data["apps"]["video_joiner"]["default_output_dir"]

    @property
    def video_joiner_default_video_name(self) -> str:
        return self.data["apps"]["video_joiner"]["default_video_name"]

    @property
    def video_joiner_default_target_duration(self) -> int:
        return self.data["apps"]["video_joiner"]["default_target_duration"]

    @property
    def video_joiner_default_end_screens_dir(self) -> str:
        return self.data["apps"]["video_joiner"]["default_end_screens_dir"]

    @property
    def video_joiner_default_random_end_screen(self) -> bool:
        return self.data["apps"]["video_joiner"]["default_random_end_screen"]

    @property
    def video_joiner_default_timestamps_prefix(self) -> str:
        return self.data["apps"]["video_joiner"]["default_timestamps_prefix"]

    @property
    def video_joiner_default_extra_description(self) -> str:
        return self.data["apps"]["video_joiner"]["default_extra_description"]

    @property
    def video_joiner_default_timestamps_secuence(self) -> list:
        return self.data["apps"]["video_joiner"]["default_timestamps_secuence"]

    # ───────────────────────────────
    # VIDEO CONVERTER @@@@
    # ───────────────────────────────

    @property
    def video_formats(self) -> dict:
        return self.data["apps"]["video_converter"]["video_formats"]

    @property
    def video_converter_src(self) -> str:
        return self.data["apps"]["video_converter"]["src"]

    @property
    def video_converter_dst_dir(self) -> str:
        return self.data["apps"]["video_converter"]["dst_dir"]

    @property
    def video_converter_output_format(self) -> str:
        return self.data["apps"]["video_converter"]["output_format"]

    @property
    def video_converter_reference_video(self) -> str:
        return self.data["apps"]["video_converter"]["reference_video"]

    # ───────────────────────────────
    # RANKING SYSTEM  @@@@
    # ───────────────────────────────

    @property
    def ranking_enabled(self) -> bool:
        return "ranking_system" in self.data["apps"]

    @property
    def ranking_system(self) -> dict:
        return self.data["apps"]["ranking_system"]

    @property
    def ranking_entity(self) -> str:
        return self.data["apps"]["ranking_system"]["entity"]

    @property
    def ranking_preset(self) -> str:
        return self.data["apps"]["ranking_system"]["preset"]

    @property
    def ranking_filters(self) -> list:
        return self.data["apps"]["ranking_system"]["filters"]

    @property
    def ranking_scope_filters(self) -> str:
        return self.data["apps"]["ranking_system"]["filters"]["scope"]

    @property
    def ranking_duel_filter(self) -> str | None:
        return self.data["apps"]["ranking_system"]["filters"]["duel"]

    @property
    def ranking_participant_filters(self) -> list:
        return self.data["apps"]["ranking_system"]["filters"]["participant_filters"]

    @property
    def ranking_battle_filters(self) -> list:
        return self.data["apps"]["ranking_system"]["filters"]["battle_filters"]

    @property
    def ranking_player_filters(self) -> list:
        return self.data["apps"]["ranking_system"]["filters"]["player_filters"]

    @property
    def ranking_season_name(self) -> str:
        return self.data["apps"]["ranking_system"]["filters"]["scope"]["season_name"]

    @property
    def ranking_event_name(self) -> str:
        return self.data["apps"]["ranking_system"]["filters"]["scope"]["event_name"]

    @property
    def ranking_event_type_name(self) -> str:
        return self.data["apps"]["ranking_system"]["filters"]["scope"]["event_type_name"]

    @property
    def ranking_region_name(self) -> str:
        return self.data["apps"]["ranking_system"]["filters"]["scope"]["region_name"]

    @property
    def ranking_game_name(self) -> str:
        return self.data["apps"]["ranking_system"]["filters"]["scope"]["game_name"]

    @property
    def ranking_game_version(self) -> str:
        return self.data["apps"]["ranking_system"]["filters"]["scope"]["game_version"]

    @property
    def ranking_event_platform(self) -> str:
        return self.data["apps"]["ranking_system"]["filters"]["scope"]["event_platform"]

    @property
    def ranking_game_franchise_name(self) -> str:
        return self.data["apps"]["ranking_system"]["filters"]["scope"]["game_franchise_name"]

    @property
    def ranking_duel_id(self) -> str:
        return self.data["apps"]["ranking_system"]["filters"]["duel"]["duel_id"]

    @property
    def ranking_duel_type_name(self) -> str:
        return self.data["apps"]["ranking_system"]["filters"]["duel"]["duel_type_name"]

    @property
    def ranking_player_name(self) -> str:
        return self.data["apps"]["ranking_system"]["filters"]["participant"]["player_name"]

    @property
    def ranking_team_name(self) -> str:
        return self.data["apps"]["ranking_system"]["filters"]["participant"]["team_name"]

    @property
    def ranking_participant_position(self) -> str:
        return self.data["apps"]["ranking_system"]["filters"]["participant"]["participant_position"]

    @property
    def ranking_stage_name(self) -> str:
        return self.data["apps"]["ranking_system"]["filters"]["battle"]["stage_name"]

    @property
    def ranking_game_character_name(self) -> str:
        return self.data["apps"]["ranking_system"]["filters"]["player"]["game_character_name"]

    @property
    def ranking_character_identity_name(self) -> str:
        return self.data["apps"]["ranking_system"]["filters"]["player"]["character_identity_name"]

    @property
    def ranking_country_iso_code(self) -> str:
        return self.data["apps"]["ranking_system"]["filters"]["player"]["country_iso_code"]

    @property
    def ranking_export_format(self) -> str:
        return self.data["apps"]["ranking_system"]["export"]["format"]

    @property
    def ranking_export_output(self) -> str:
        return self.data["apps"]["ranking_system"]["export"]["output"]
