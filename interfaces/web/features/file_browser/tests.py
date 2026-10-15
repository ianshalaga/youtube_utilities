
import tempfile
from pathlib import Path

from django.test import TestCase

# from .services import FileBrowserService


class FileBrowserViewTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp_dir.name)
        (self.directory / "songs").mkdir()
        (self.directory / "track.mp3").write_text("test")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_list_drives(self):
        response = self.client.get(
            "/file-browser/",
            {"action": "drives"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("entries", response.json())

    def test_list_directory(self):
        response = self.client.get(
            "/file-browser/",
            {
                "action": "list",
                "path": str(self.directory),
            },
        )

        self.assertEqual(response.status_code, 200)

        entries = response.json()["entries"]
        names = {entry["name"] for entry in entries}

        self.assertEqual(names, {"songs", "track.mp3"})

    def test_list_directories_only(self):
        response = self.client.get(
            "/file-browser/",
            {
                "action": "list",
                "path": str(self.directory),
                "show_files": "false",
            },
        )

        self.assertEqual(response.status_code, 200)

        entries = response.json()["entries"]

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["name"], "songs")

    def test_invalid_directory(self):
        response = self.client.get(
            "/file-browser/",
            {
                "action": "list",
                "path": str(self.directory / "does-not-exist"),
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_select_directory(self):
        response = self.client.post(
            "/file-browser/select/",
            {
                "path": str(self.directory),
                "type": "directory",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["selection"]["path"],
            str(self.directory.resolve()),
        )

    def test_select_file(self):
        file_path = self.directory / "track.mp3"

        response = self.client.post(
            "/file-browser/select/",
            {
                "path": str(file_path),
                "type": "file",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["selection"]["path"],
            str(file_path.resolve()),
        )

    def test_reject_wrong_selection_type(self):
        response = self.client.post(
            "/file-browser/select/",
            {
                "path": str(self.directory),
                "type": "file",
            },
        )

        self.assertEqual(response.status_code, 400)
