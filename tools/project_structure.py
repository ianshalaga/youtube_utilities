from pathlib import Path


# Project root: tools/project/project_structure.py -> project root
BASE_DIR = Path(__file__).resolve().parents[1]

# Default output file
OUTPUT_NAME = "structure_minimal.txt"

# Same exclusions as the original PowerShell script.
EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    "venv",
    "env",
    "static",
}

# Same file types as the original PowerShell script.
INCLUDED_NAMES = {
    "requirements.txt",
    "pyproject.toml",
}

INCLUDED_EXTENSIONS = {
    ".py",
    ".md",
}


def should_exclude(path: Path) -> bool:
    """Return True when any path component belongs to an excluded directory."""
    return any(part in EXCLUDED_DIRS for part in path.parts)


def collect_files(base_dir: Path) -> list[Path]:
    """Collect project files using the same filters as the original script."""
    files = []

    for path in base_dir.rglob("*"):
        if not path.is_file():
            continue

        if should_exclude(path.relative_to(base_dir)):
            continue

        if path.suffix in INCLUDED_EXTENSIONS or path.name in INCLUDED_NAMES:
            files.append(path)

    return sorted(files, key=lambda path: path.relative_to(base_dir).as_posix().lower())


def export_structure(base_dir: Path, output_path: Path) -> None:
    """Export one relative file path per line."""
    files = collect_files(base_dir)

    output_path.write_text(
        "\n".join(
            path.relative_to(base_dir).as_posix()
            for path in files
        ) + ("\n" if files else ""),
        encoding="utf-8",
    )

    print(f"Project structure exported to: {output_path}")
    print(f"Total files: {len(files)}")


if __name__ == "__main__":
    export_structure(
        base_dir=BASE_DIR,
        output_path=BASE_DIR / "tools" / OUTPUT_NAME,
    )
