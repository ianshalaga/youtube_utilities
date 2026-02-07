from pathlib import Path
from typing import Iterable, Set

DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    "venv",
    ".venv",
    "env",
    ".env",
    "node_modules",
    "dist",
    "build",
}

DEFAULT_EXTENSIONS = {".py"}


def should_exclude(path: Path, excluded_dirs: Set[str]) -> bool:
    return any(part in excluded_dirs for part in path.parts)


def collect_files(
    root: Path,
    extensions: Set[str],
    excluded_dirs: Set[str],
) -> list[Path]:
    files = []
    for path in root.rglob("*"):
        if path.is_file():
            if should_exclude(path, excluded_dirs):
                continue
            if path.suffix in extensions:
                files.append(path)
    return sorted(files)


def build_tree(files: Iterable[Path], root: Path) -> str:
    tree = {}
    for file in files:
        rel = file.relative_to(root)
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


def export_context(
    root_dir: str,
    output_file: str = "project_context.txt",
    extensions: Set[str] = None,
    excluded_dirs: Set[str] = None,
):
    root = Path(root_dir).resolve()
    extensions = extensions or DEFAULT_EXTENSIONS
    excluded_dirs = excluded_dirs or DEFAULT_EXCLUDED_DIRS

    files = collect_files(root, extensions, excluded_dirs)

    with open(output_file, "w", encoding="utf-8") as out:
        out.write("# PROJECT STRUCTURE\n\n")
        out.write(build_tree(files, root))
        out.write("\n\n# FILES\n\n")

        for file in files:
            rel_path = file.relative_to(root)
            out.write("=" * 80 + "\n")
            out.write(f"FILE: {rel_path}\n")
            out.write("=" * 80 + "\n")
            try:
                out.write(file.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                out.write("[ERROR: Could not decode file]")
            out.write("\n\n")


if __name__ == "__main__":
    import sys

    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    export_context(
        root_dir=target_dir,
        output_file="project_context.txt",
        extensions={".py"},  # podés agregar ".md", ".yml", etc
    )
