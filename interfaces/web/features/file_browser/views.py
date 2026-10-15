from pathlib import Path

from django.http import JsonResponse
from django.views import View
from django.shortcuts import render

from .services import (
    FileBrowserError,
    FileBrowserService,
    InvalidPathError,
    PermissionDeniedError,
)

from core.config_manager import ConfigManager


class FileBrowserView(View):
    """Expose filesystem browsing operations through HTTP."""

    
    @staticmethod
    def _resolve_default_directory(
        path: str | Path,
        *,
        is_file_path: bool = False,
    ) -> Path:
        """Find the closest existing directory, ascending from a path."""
        candidate = Path(path).expanduser()

        if is_file_path:
            candidate = candidate.parent

        while True:
            try:
                if candidate.is_dir():
                    return candidate.resolve(strict=True)
            except (OSError, RuntimeError, ValueError):
                pass

            parent = candidate.parent

            if parent == candidate:
                raise InvalidPathError(
                    f"No existing directory could be found for: {path}"
                )

            candidate = parent


    def get(self, request):
        action = request.GET.get("action")

        if action is None:
            return render(
                request,
                "file_browser/browse.html",
            )
            
        browser = FileBrowserService()

        if action == "default":
            target = request.GET.get("target", "").lower()
            config = ConfigManager()

            if target == "audios":
                configured_path = config.video_music_default_audios_dir
            elif target == "video":
                configured_path = config.video_music_default_video_path
            else:
                return JsonResponse({
                    "error": "Target must be 'audios' or 'video'.",
                }, status=400)

            try:
                directory = self._resolve_default_directory(
                    configured_path,
                    is_file_path=(target == "video"),
                )

                return JsonResponse({
                    "path": str(directory),
                    "entries": browser.list_directory(directory),
                })

            except InvalidPathError as exc:
                return JsonResponse({"error": str(exc)}, status=400)
            except PermissionDeniedError as exc:
                return JsonResponse({"error": str(exc)}, status=403)
            except FileBrowserError as exc:
                return JsonResponse({"error": str(exc)}, status=400)

        try:
            if action == "drives":
                return JsonResponse({
                    "entries": browser.list_drives(),
                })

            if action == "list":
                path = request.GET.get("path")

                if not path:
                    return JsonResponse({
                        "error": "A directory path is required.",
                    }, status=400)

                show_files = (
                    request.GET.get("show_files", "true").lower()
                    in {"true", "1", "yes"}
                )

                return JsonResponse({
                    "path": str(Path(path)),
                    "entries": browser.list_directory(
                        path,
                        show_files=show_files,
                    ),
                })

            return JsonResponse({
                "error": f"Unknown action: {action}",
            }, status=400)

        except InvalidPathError as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        except PermissionDeniedError as exc:
            return JsonResponse({"error": str(exc)}, status=403)
        except FileBrowserError as exc:
            return JsonResponse({"error": str(exc)}, status=400)


class FileBrowserSelectionView(View):
    """Validate a file or directory selection."""

    def post(self, request):
        path = request.POST.get("path", "")
        entry_type = request.POST.get("type", "")

        if entry_type not in {"file", "directory"}:
            return JsonResponse({
                "error": "Type must be 'file' or 'directory'.",
            }, status=400)

        browser = FileBrowserService()

        try:
            entry = browser.get_entry(
                path,
                expected_type=entry_type,
            )

            return JsonResponse({"selection": entry})

        except InvalidPathError as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        except PermissionDeniedError as exc:
            return JsonResponse({"error": str(exc)}, status=403)
        except FileBrowserError as exc:
            return JsonResponse({"error": str(exc)}, status=400)
