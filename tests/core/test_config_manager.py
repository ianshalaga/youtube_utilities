import json
from pathlib import Path

from core.config_manager import ConfigManager


def test_update_video_music_defaults_normalizes_string_paths_to_posix(monkeypatch, tmp_path):
    test_config = {
        "apps": {
            "video_music": {
                "max_items_per_dir": 15,
                "default_audios_dir": "old/path",
                "default_video_path": "old/video.mp4",
                "default_output_dir": "old_output",
            }
        }
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(test_config), encoding="utf-8")

    monkeypatch.setattr(ConfigManager, "CONFIG_FILE", config_file)

    manager = ConfigManager()
    manager.update_video_music_defaults(
        max_items_per_dir=20,
        default_audios_dir=r"D:\audios\folder",
        default_video_path=r"D:\videos\base.mp4",
        default_output_dir=r"sub\output",
    )

    saved_data = json.loads(config_file.read_text(encoding="utf-8"))
    settings = saved_data["apps"]["video_music"]

    assert settings["max_items_per_dir"] == 20
    assert settings["default_audios_dir"] == "D:/audios/folder"
    assert settings["default_video_path"] == "D:/videos/base.mp4"
    assert settings["default_output_dir"] == "sub/output"
    assert "\\" not in settings["default_audios_dir"]
    assert "\\" not in settings["default_video_path"]
    assert "\\" not in settings["default_output_dir"]


def test_update_video_music_defaults_accepts_path_instances(monkeypatch, tmp_path):
    test_config = {
        "apps": {
            "video_music": {
                "max_items_per_dir": 15,
                "default_audios_dir": "old/path",
                "default_video_path": "old/video.mp4",
                "default_output_dir": "old_output",
            }
        }
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(test_config), encoding="utf-8")

    monkeypatch.setattr(ConfigManager, "CONFIG_FILE", config_file)

    manager = ConfigManager()
    manager.update_video_music_defaults(
        max_items_per_dir=10,
        default_audios_dir=Path(r"D:\audios\folder"),
        default_video_path=Path(r"D:\videos\base.mp4"),
        default_output_dir=Path(r"sub\output"),
    )

    saved_data = json.loads(config_file.read_text(encoding="utf-8"))
    settings = saved_data["apps"]["video_music"]

    assert settings["max_items_per_dir"] == 10
    assert settings["default_audios_dir"] == "D:/audios/folder"
    assert settings["default_video_path"] == "D:/videos/base.mp4"
    assert settings["default_output_dir"] == "sub/output"
