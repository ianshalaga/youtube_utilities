from pathlib import Path

from django.http import JsonResponse
from django.views import View

from .services import (
    FileBrowserError,
    FileBrowserService,
    InvalidPathError,
    PermissionDeniedError,
)


class FileBrowserView(View):
    """Expose filesystem browsing operations through HTTP."""

    def get(self, request):
        action = request.GET.get("action", "list")
        browser = FileBrowserService()

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
