from datetime import datetime
from pathlib import Path
import pytest

from tools.export_context import ContextExporter


def test_get_available_targets_returns_expected_list():
    exporter = ContextExporter()
    targets = exporter.get_available_targets()

    assert "all" in targets
    assert "video_music" in targets
    assert "video_joiner" in targets
    assert "youtube_video_manager" in targets
    assert "ranking_system" in targets
    assert "video_converter" in targets
    assert "web" in targets


def test_export_unknown_target_raises_value_error(tmp_path):
    exporter = ContextExporter(base_dir=tmp_path)

    with pytest.raises(ValueError, match="Objetivo desconocido"):
        exporter.export("invalid_app", output_dir=tmp_path)


def test_export_generates_markdown_with_tree_and_content(tmp_path):
    base_dir = tmp_path / "project"
    base_dir.mkdir()

    app_dir = base_dir / "applications" / "video_music"
    app_dir.mkdir(parents=True)
    file1 = app_dir / "processor.py"
    file1.write_text("class Processor:\n    pass\n", encoding="utf-8")

    core_dir = base_dir / "core"
    core_dir.mkdir(parents=True)
    file2 = core_dir / "config_manager.py"
    file2.write_text("class ConfigManager:\n    pass\n", encoding="utf-8")

    config_file = base_dir / "config.json"
    config_file.write_text('{"app": "test"}', encoding="utf-8")

    out_dir = tmp_path / "custom_contexts"

    fixed_time = datetime(2026, 11, 23, 15, 30, 45)
    exporter = ContextExporter(base_dir=base_dir)
    result_path = exporter.export(
        target="video_music",
        output_dir=out_dir,
        timestamp=fixed_time,
        output_format="md",
    )

    assert result_path.exists()
    assert result_path.name == "context_video_music_20261123_153045.md"

    content = result_path.read_text(encoding="utf-8")

    assert "# Context Snapshot: video_music" in content
    assert "- **Project**: YouTube Utilities" in content
    assert "- **Target**: video_music" in content
    assert "- **Generated At**: 2026-11-23 15:30:45" in content
    assert "- **Total Files**: 3" in content
    assert "## Project Structure" in content
    assert "applications" in content
    assert "processor.py" in content
    assert "### File: `applications/video_music/processor.py`" in content
    assert "```python\nclass Processor:\n    pass\n\n```" in content
    assert "### File: `config.json`" in content
    assert '```json\n{"app": "test"}\n```' in content


def test_export_fenced_code_escalates_backticks_when_content_contains_code_blocks(tmp_path):
    base_dir = tmp_path / "project"
    base_dir.mkdir()
    doc_file = base_dir / "README.md"
    doc_file.write_text("Here is code:\n```python\nprint(1)\n```\n", encoding="utf-8")

    exporter = ContextExporter(base_dir=base_dir)
    out_dir = tmp_path / "output"
    result_path = exporter.export(
        target="all",
        output_dir=out_dir,
        output_format="md",
    )

    content = result_path.read_text(encoding="utf-8")
    assert "````markdown" in content
    assert "````" in content


def test_export_excludes_tests_when_include_tests_is_false(tmp_path):
    base_dir = tmp_path / "project"
    base_dir.mkdir()

    app_dir = base_dir / "applications" / "video_music"
    app_dir.mkdir(parents=True)
    (app_dir / "processor.py").write_text("code = 1", encoding="utf-8")

    tests_dir = base_dir / "tests" / "applications" / "video_music"
    tests_dir.mkdir(parents=True)
    (tests_dir / "test_processor.py").write_text("def test_one(): pass", encoding="utf-8")

    exporter = ContextExporter(base_dir=base_dir)
    out_dir = tmp_path / "output"

    result_with_tests = exporter.export(
        target="video_music",
        output_dir=out_dir,
        include_tests=True,
    )
    content_with = result_with_tests.read_text(encoding="utf-8")
    assert "test_processor.py" in content_with

    result_without_tests = exporter.export(
        target="video_music",
        output_dir=out_dir,
        include_tests=False,
    )
    content_without = result_without_tests.read_text(encoding="utf-8")
    assert "test_processor.py" not in content_without
    assert "processor.py" in content_without


def test_export_txt_format(tmp_path):
    base_dir = tmp_path / "project"
    base_dir.mkdir()
    (base_dir / "file.py").write_text("print('hello')", encoding="utf-8")

    exporter = ContextExporter(base_dir=base_dir)
    out_dir = tmp_path / "output"
    result_path = exporter.export(
        target="all",
        output_dir=out_dir,
        output_format="txt",
    )

    assert result_path.suffix == ".txt"
    content = result_path.read_text(encoding="utf-8")
    assert "FILE: file.py" in content
    assert "================================================================================" in content


def test_export_creates_default_data_contexts_directory(tmp_path):
    base_dir = tmp_path / "project"
    base_dir.mkdir()
    (base_dir / "file.py").write_text("x = 42", encoding="utf-8")

    exporter = ContextExporter(base_dir=base_dir)
    default_contexts_dir = base_dir / "data" / "contexts"
    assert not default_contexts_dir.exists()

    result_path = exporter.export(target="all")

    assert default_contexts_dir.exists()
    assert result_path.parent == default_contexts_dir
