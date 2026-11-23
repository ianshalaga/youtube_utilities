"""
Herramienta de exportación de contexto de código para modelos LLM.

Permite generar un volcado estructurado en Markdown (.md) o texto (.txt)
del contexto de una aplicación específica o del proyecto completo.
"""

from datetime import datetime
import fnmatch
from pathlib import Path
from typing import Iterable, Set


class ContextExporter:
    """Exporta el código y estructura del proyecto optimizado para LLMs."""

    DEFAULT_EXCLUDED_DIRS = {
        ".git",
        ".hg",
        ".svn",
        ".idea",
        ".vscode",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "venv",
        ".venv",
        "env",
        ".env",
        "node_modules",
        "dist",
        "build",
        ".tox",
        "data",
        "temp",
    }

    DEFAULT_EXTENSIONS = {
        ".py",
        ".md",
        ".txt",
        ".yml",
        ".yaml",
        ".toml",
        ".json",
        ".html",
        ".css",
        ".js",
        ".sql",
    }

    DEFAULT_EXCLUDED_PATTERNS = {
        "*.pyc",
        "*.pyo",
        "*.pyd",
        "*~",
        "*.min.py",
        "*.sqlite3",
        "*.db",
        "package-lock.json",
    }

    LANGUAGE_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".md": "markdown",
        ".sql": "sql",
        ".sh": "bash",
        ".bat": "batch",
        ".ps1": "powershell",
    }

    AVAILABLE_TARGETS = [
        "all",
        "video_music",
        "video_joiner",
        "youtube_video_manager",
        "ranking_system",
        "video_converter",
        "web",
    ]

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = (base_dir or Path(__file__).resolve().parents[1]).resolve()
        self.default_output_dir = self.base_dir / "data" / "contexts"

    def get_available_targets(self) -> list[str]:
        """Retorna la lista de aplicaciones y objetivos válidos."""
        return list(self.AVAILABLE_TARGETS)

    def _get_target_paths(self, target: str) -> tuple[Path, ...]:
        """Obtiene las rutas asociadas a un objetivo o aplicación."""
        common_core = (
            self.base_dir / "config.json",
            self.base_dir / "core/config_manager.py",
        )

        catalog: dict[str, tuple[Path, ...]] = {
            "all": (self.base_dir,),
            "video_music": common_core + (
                self.base_dir / "core/time_utils.py",
                self.base_dir / "applications/video_music",
                self.base_dir / "composition/video_music.py",
                self.base_dir / "domain/media",
                self.base_dir / "services/media",
                self.base_dir / "services/filesystem",
                self.base_dir / "services/system",
                self.base_dir / "interfaces/cli/builders/video_music_input_builder.py",
                self.base_dir / "interfaces/cli/presenters/video_music_result_presenter.py",
                self.base_dir / "interfaces/web/apps/video_music_web",
                self.base_dir / "interfaces/web/static/video_music_web",
                self.base_dir / "tests/applications/video_music",
                self.base_dir / "tests/composition/test_video_music.py",
                self.base_dir / "tests/interfaces/cli/builders/test_video_music_input_builder.py",
                self.base_dir / "tests/interfaces/cli/presenters/test_video_music_result_presenter.py",
                self.base_dir / "tests/interfaces/web/apps/video_music_web",
            ),
            "video_joiner": common_core + (
                self.base_dir / "core/time_utils.py",
                self.base_dir / "applications/video_joiner",
                self.base_dir / "domain/media",
                self.base_dir / "services/media",
                self.base_dir / "services/system",
                self.base_dir / "interfaces/web/apps/video_joiner_web",
                self.base_dir / "tests/applications/video_joiner",
            ),
            "youtube_video_manager": common_core + (
                self.base_dir / "config/youtube",
                self.base_dir / "applications/youtube_video_manager",
                self.base_dir / "composition/youtube_video_manager.py",
                self.base_dir / "domain/youtube",
                self.base_dir / "services/youtube",
                self.base_dir / "interfaces/cli/menus",
                self.base_dir / "tests/applications/youtube_video_manager",
                self.base_dir / "tests/composition/test_youtube_video_manager.py",
                self.base_dir / "tests/domain/youtube",
                self.base_dir / "tests/services/youtube",
                self.base_dir / "tests/interfaces/cli/menus",
                self.base_dir / "tests/integration/youtube",
            ),
            "ranking_system": common_core + (
                self.base_dir / "applications/ranking_system",
                self.base_dir / "domain/ranking",
                self.base_dir / "services/ranking",
            ),
            "video_converter": common_core + (
                self.base_dir / "services/media/video/converter.py",
                self.base_dir / "interfaces/web/apps/audio_converter_web",
            ),
            "web": (
                self.base_dir / "interfaces/web",
                self.base_dir / "tests/interfaces/web",
            ),
        }

        if target not in catalog:
            valid = ", ".join(self.AVAILABLE_TARGETS)
            raise ValueError(
                f"Objetivo desconocido: '{target}'. Opciones válidas: {valid}"
            )

        return catalog[target]

    def _should_exclude_dir(self, path: Path, excluded_dirs: Set[str]) -> bool:
        """Determina si un directorio debe ser ignorado."""
        return any(part in excluded_dirs for part in path.parts)

    def _should_exclude_pattern(self, path: Path, patterns: Set[str]) -> bool:
        """Determina si el nombre de archivo coincide con algún patrón de exclusión."""
        return any(fnmatch.fnmatch(path.name, pattern) for pattern in patterns)

    def _collect_files(
        self,
        input_paths: Iterable[Path],
        *,
        include_tests: bool = True,
        extensions: Set[str] | None = None,
        excluded_dirs: Set[str] | None = None,
        excluded_patterns: Set[str] | None = None,
    ) -> list[Path]:
        """Recolecta y filtra todos los archivos de código válidos."""
        extensions = extensions or self.DEFAULT_EXTENSIONS
        excluded_dirs = excluded_dirs or self.DEFAULT_EXCLUDED_DIRS
        excluded_patterns = set(excluded_patterns or self.DEFAULT_EXCLUDED_PATTERNS)

        if not include_tests:
            excluded_patterns.update({"test_*.py", "*_test.py"})

        collected: set[Path] = set()

        for raw_path in input_paths:
            path = raw_path.resolve() if not raw_path.is_absolute() else raw_path
            if not path.exists():
                continue

            if not include_tests and "tests" in path.parts:
                continue

            if path.is_file():
                if (
                    path.suffix in extensions
                    and not self._should_exclude_dir(path, excluded_dirs)
                    and not self._should_exclude_pattern(path, excluded_patterns)
                ):
                    collected.add(path.resolve())
            elif path.is_dir():
                for item in path.rglob("*"):
                    if not item.is_file():
                        continue
                    if not include_tests and "tests" in item.parts:
                        continue
                    if self._should_exclude_dir(item, excluded_dirs):
                        continue
                    if self._should_exclude_pattern(item, excluded_patterns):
                        continue
                    if item.suffix in extensions:
                        collected.add(item.resolve())

        return sorted(collected, key=lambda p: str(p.relative_to(self.base_dir)).lower())

    def _build_tree(self, files: Iterable[Path]) -> str:
        """Construye una representación en árbol de la estructura de archivos."""
        tree: dict = {}

        for file in files:
            rel = file.relative_to(self.base_dir)
            current = tree
            for part in rel.parts:
                current = current.setdefault(part, {})

        def render(node: dict, indent: int = 0) -> list[str]:
            lines = []
            for key in sorted(node):
                lines.append("  " * indent + key)
                lines.extend(render(node[key], indent + 1))
            return lines

        return "\n".join(render(tree))

    def _format_fenced_code(self, content: str, extension: str) -> str:
        """Envuelve el contenido en un bloque cercado de Markdown sin colisiones."""
        lang = self.LANGUAGE_MAP.get(extension, "")
        fence = "```"
        if "```" in content:
            fence = "````"
            while fence in content:
                fence += "`"
        return f"{fence}{lang}\n{content}\n{fence}"

    def _generate_content(
        self,
        target: str,
        files: list[Path],
        output_format: str = "md",
        timestamp: datetime | None = None,
    ) -> str:
        """Genera el texto completo del contexto para LLMs."""
        ref_time = timestamp or datetime.now()
        now_str = ref_time.strftime("%Y-%m-%d %H:%M:%S")
        tree_str = self._build_tree(files)

        lines: list[str] = [
            f"# Context Snapshot: {target}",
            f"- **Project**: YouTube Utilities",
            f"- **Target**: {target}",
            f"- **Generated At**: {now_str}",
            f"- **Total Files**: {len(files)}",
            f"- **Base Directory**: {self.base_dir.as_posix()}",
            "",
            "## Project Structure",
            "",
            "```text",
            tree_str,
            "```",
            "",
            "## Files Content",
            "",
        ]

        for file in files:
            rel_path = file.relative_to(self.base_dir).as_posix()
            lines.append("---")
            lines.append(f"### File: `{rel_path}`")
            lines.append("")

            try:
                content = file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = "[ERROR: No se pudo decodificar el archivo como UTF-8]"

            if output_format == "md":
                lines.append(self._format_fenced_code(content, file.suffix))
            else:
                lines.append(f"FILE: {rel_path}")
                lines.append("=" * 80)
                lines.append(content)

            lines.append("")

        return "\n".join(lines)

    def export(
        self,
        target: str = "all",
        output_dir: Path | None = None,
        *,
        include_tests: bool = True,
        output_format: str = "md",
        timestamp: datetime | None = None,
    ) -> Path:
        """
        Ejecuta la recolección y exporta el contexto a un archivo en data/contexts.

        Args:
            target: Nombre de la aplicación u 'all' para todo el proyecto.
            output_dir: Directorio de destino (por defecto data/contexts).
            include_tests: Si es True, incluye archivos y directorios de pruebas.
            output_format: 'md' (Markdown) o 'txt' (texto plano).
            timestamp: Fecha/hora de referencia para nombrado y metadatos.

        Returns:
            Path del archivo exportado.
        """
        target = target.strip().lower()
        target_paths = self._get_target_paths(target)

        files = self._collect_files(
            target_paths,
            include_tests=include_tests,
        )

        out_dir = output_dir or self.default_output_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        ref_time = timestamp or datetime.now()
        date_id = ref_time.strftime("%Y%m%d_%H%M%S")
        file_extension = "md" if output_format == "md" else "txt"
        file_name = f"context_{target}_{date_id}.{file_extension}"
        output_file = out_dir / file_name

        payload = self._generate_content(
            target=target,
            files=files,
            output_format=output_format,
            timestamp=ref_time,
        )

        output_file.write_text(payload, encoding="utf-8")
        return output_file


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Exporta el contexto del proyecto para modelos LLM.",
    )
    parser.add_argument(
        "target",
        nargs="?",
        default="all",
        choices=ContextExporter.AVAILABLE_TARGETS,
        help="Aplicación u objetivo a exportar (por defecto: all).",
    )
    parser.add_argument(
        "--no-tests",
        action="store_true",
        help="Excluye los archivos de pruebas del volcado.",
    )
    parser.add_argument(
        "--format",
        choices=["md", "txt"],
        default="md",
        help="Formato de salida (md o txt, por defecto: md).",
    )

    args = parser.parse_args()

    exporter = ContextExporter()
    exported_path = exporter.export(
        target=args.target,
        include_tests=not args.no_tests,
        output_format=args.format,
    )
    print(f"Contexto generado exitosamente en: {exported_path}")
