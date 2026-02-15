import fnmatch
import hashlib
import json
from pathlib import Path
from typing import Iterable, Set
from collections.abc import Iterable


BASE_DIR = Path(__file__).resolve().parents[1]


# BASE_DIR / <path>
INPUT_PATHS = (
    # BASE_DIR / "services/ranking/loaders/legacy/row_legacy_mapper.py",
    # BASE_DIR / "services/ranking/loaders/legacy/row_legacy_dto.py",
    BASE_DIR / "services/ranking/storage/models",
)

FILE_NAME = "ranking_models_context"

OUTPUT_NAME = Path("tools") / f"{FILE_NAME}"

# ============================================================
# CONFIGURACIÓN DEFAULT (Python Projects)
# ============================================================

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
}

DEFAULT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".toml",
}

DEFAULT_EXCLUDED_PATTERNS = {
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*~",
    "*.min.py",
    "*_test.py",
    "test_*.py",
}

# ============================================================
# FILTROS
# ============================================================


def should_exclude_dir(path: Path, excluded_dirs: Set[str]) -> bool:
    return any(part in excluded_dirs for part in path.parts)


def should_exclude_pattern(path: Path, patterns: Set[str]) -> bool:
    return any(fnmatch.fnmatch(path.name, pattern) for pattern in patterns)


# ============================================================
# UTILIDADES
# ============================================================

def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ============================================================
# COLECTOR DE ARCHIVOS
# ============================================================

def collect_from_inputs(
    inputs: Iterable[Path],
    extensions: Set[str],
    excluded_dirs: Set[str],
    excluded_patterns: Set[str],
    strict: bool = False,
) -> list[Path]:
    files: set[Path] = set()

    for input_path in inputs:
        if not input_path.exists():
            if strict:
                raise FileNotFoundError(input_path)
            continue

        if input_path.is_file():
            if (
                input_path.suffix in extensions
                and not should_exclude_dir(input_path, excluded_dirs)
                and not should_exclude_pattern(input_path, excluded_patterns)
            ):
                files.add(input_path.resolve())

        elif input_path.is_dir():
            for path in input_path.rglob("*"):
                if not path.is_file():
                    continue
                if should_exclude_dir(path, excluded_dirs):
                    continue
                if should_exclude_pattern(path, excluded_patterns):
                    continue
                if path.suffix in extensions:
                    files.add(path.resolve())

    return sorted(files)


# ============================================================
# ÁRBOL DE ESTRUCTURA
# ============================================================

def build_tree(files: Iterable[Path], base_dir: Path) -> str:
    tree = {}

    for file in files:
        rel = file.relative_to(base_dir)
        current = tree
        for part in rel.parts:
            current = current.setdefault(part, {})

    def render(node, indent=0):
        lines = []
        for key in sorted(node):
            lines.append("  " * indent + key)
            lines.extend(render(node[key], indent + 1))
        return lines

    return "\n".join(render(tree))


# ============================================================
# EXPORT PRINCIPAL (TXT + JSON)
# ============================================================

def export_context(
    base_dir: Path,
    input_paths: Iterable[Path] | Path,
    output_path: str,
    extensions: Set[str] = None,
    excluded_dirs: Set[str] = None,
    excluded_patterns: Set[str] = None,
    strict: bool = False,
):
    # --- NORMALIZACIÓN ---
    if isinstance(input_paths, (Path, str)):
        input_paths = (Path(input_paths),)

    extensions = extensions or DEFAULT_EXTENSIONS
    excluded_dirs = excluded_dirs or DEFAULT_EXCLUDED_DIRS
    excluded_patterns = excluded_patterns or DEFAULT_EXCLUDED_PATTERNS

    files = collect_from_inputs(
        inputs=input_paths,
        extensions=extensions,
        excluded_dirs=excluded_dirs,
        excluded_patterns=excluded_patterns,
        strict=strict,
    )

    txt_path = Path(f"{output_path}.txt")
    json_path = Path(f"{output_path}.json")

    # =========================
    # TXT
    # =========================
    with txt_path.open("w", encoding="utf-8") as out:
        out.write("# GENERATED PROJECT CONTEXT\n")
        out.write(f"# base_dir: {base_dir}\n")
        out.write(f"# total_files: {len(files)}\n\n")

        out.write("# PROJECT STRUCTURE\n\n")
        out.write(build_tree(files, base_dir))
        out.write("\n\n# FILES\n\n")

        for file in files:
            rel = file.relative_to(base_dir)
            out.write("=" * 80 + "\n")
            out.write(f"FILE: {rel}\n")
            out.write("=" * 80 + "\n")
            try:
                out.write(file.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                out.write("[ERROR: Could not decode file]")
            out.write("\n\n")

    # =========================
    # JSON
    # =========================
    json_payload = {
        "base_dir": str(base_dir),
        "extensions": sorted(extensions),
        "excluded_dirs": sorted(excluded_dirs),
        "excluded_patterns": sorted(excluded_patterns),
        "total_files": len(files),
        "files": [],
    }

    for file in files:
        rel = file.relative_to(base_dir)
        try:
            content = file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = None

        json_payload["files"].append(
            {
                "path": str(rel),
                "extension": file.suffix,
                "size_bytes": file.stat().st_size,
                "lines": content.count("\n") + 1 if content else None,
                "sha256": file_hash(file),
                "content": content,
            }
        )

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(json_payload, f, indent=2, ensure_ascii=False)


# ============================================================
# CONFIGURACIÓN MANUAL
# ============================================================

if __name__ == "__main__":
    export_context(
        base_dir=BASE_DIR,
        input_paths=INPUT_PATHS,
        output_path=OUTPUT_NAME,
        strict=True,
    )
