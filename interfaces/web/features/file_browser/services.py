import os
from pathlib import Path
from typing import Literal


EntryType = Literal["directory", "file"]


class FileBrowserError(Exception):
    """Base exception for file browser errors."""


class InvalidPathError(FileBrowserError):
    """Raised when a path does not exist or is invalid."""


class PermissionDeniedError(FileBrowserError):
    """Raised when a path cannot be accessed due to permissions."""


class FileBrowserService:
    """Explore the filesystem accessible to the current process."""

    def list_drives(self) -> list[dict[str, str]]:
        """
        Return available Windows drives.

        On non-Windows systems, return the filesystem root.
        """
        if os.name == "nt":
            import string

            drives = []

            for letter in string.ascii_uppercase:
                drive = Path(f"{letter}:/")

                if drive.exists():
                    drives.append(
                        {
                            "name": f"{letter}:",
                            "path": str(drive),
                            "type": "drive",
                        }
                    )

            return drives

        root = Path("/")

        return [
            {
                "name": "/",
                "path": str(root),
                "type": "drive",
            }
        ]

    def list_directory(
        self,
        path: str | Path,
        *,
        show_files: bool = True,
    ) -> list[dict[str, str]]:
        """
        List the immediate contents of a directory.

        Directories are listed first, followed by files.
        Hidden entries are not excluded automatically.
        """
        directory = self._resolve_directory(path)

        try:
            entries = list(directory.iterdir())
        except PermissionError as exc:
            raise PermissionDeniedError(
                f"Permission denied: {directory}"
            ) from exc
        except OSError as exc:
            raise FileBrowserError(
                f"Unable to read directory: {directory}"
            ) from exc

        results = []

        for entry in entries:
            try:
                if entry.is_dir():
                    results.append(
                        {
                            "name": entry.name,
                            "path": str(entry),
                            "type": "directory",
                        }
                    )
                elif show_files and entry.is_file():
                    results.append(
                        {
                            "name": entry.name,
                            "path": str(entry),
                            "type": "file",
                        }
                    )
            except PermissionError:
                # An inaccessible entry should not prevent listing
                # the remaining entries.
                continue
            except OSError:
                continue

        results.sort(
            key=lambda item: (
                item["type"] != "directory",
                item["name"].casefold(),
            )
        )

        return results

    def get_entry(
        self,
        path: str | Path,
        *,
        expected_type: EntryType,
    ) -> dict[str, str]:
        """Validate a selected file or directory and return its metadata."""
        entry = self._resolve_path(path)

        try:
            if expected_type == "directory" and not entry.is_dir():
                raise InvalidPathError(
                    f"Expected a directory: {entry}"
                )

            if expected_type == "file" and not entry.is_file():
                raise InvalidPathError(
                    f"Expected a file: {entry}"
                )
        except PermissionError as exc:
            raise PermissionDeniedError(
                f"Permission denied: {entry}"
            ) from exc
        except OSError as exc:
            raise FileBrowserError(
                f"Unable to access path: {entry}"
            ) from exc

        return {
            "name": entry.name or str(entry),
            "path": str(entry),
            "type": expected_type,
        }

    @staticmethod
    def _resolve_path(path: str | Path) -> Path:
        """Validate and normalize a filesystem path."""
        if not str(path).strip():
            raise InvalidPathError("Path cannot be empty.")

        try:
            resolved = Path(path).resolve(strict=True)
        except (OSError, RuntimeError, ValueError) as exc:
            raise InvalidPathError(
                f"Invalid or inaccessible path: {path}"
            ) from exc

        return resolved

    def _resolve_directory(self, path: str | Path) -> Path:
        """Validate that the supplied path is an accessible directory."""
        directory = self._resolve_path(path)

        try:
            if not directory.is_dir():
                raise InvalidPathError(
                    f"Path is not a directory: {directory}"
                )
        except PermissionError as exc:
            raise PermissionDeniedError(
                f"Permission denied: {directory}"
            ) from exc
        except OSError as exc:
            raise FileBrowserError(
                f"Unable to access directory: {directory}"
            ) from exc

        return directory
