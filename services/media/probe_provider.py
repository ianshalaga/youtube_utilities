from pathlib import Path
import subprocess
import json
from domain.media.base import MediaProbeProvider
from core.config_manager import ConfigManager

config = ConfigManager()


class FFprobeMediaProbeProvider(MediaProbeProvider):
    def __init__(self):
        self._cache = {}

    def _probe(self, path: Path) -> dict:
        if path not in self._cache:
            cmd = [
                config.paths_probe,
                "-v", "error",
                "-show_format",
                "-show_streams",
                "-of", "json",
                str(path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            self._cache[path] = json.loads(result.stdout)
        return self._cache[path]

    def duration(self, path: Path) -> float:
        data = self._probe(path)
        return float(data["format"]["duration"])
