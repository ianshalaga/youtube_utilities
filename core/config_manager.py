import json
from pathlib import Path


class ConfigManager:
    FILE = Path("config.json")

    def __init__(self):
        if not self.FILE.exists():
            raise FileNotFoundError("config.json no encontrado")
        self.data = json.loads(self.FILE.read_text(encoding="utf-8"))

    def save(self):
        self.FILE.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    # Helpers semánticos (MUY recomendable)
    @property
    def output_dir(self) -> Path:
        return Path(self.data["output"]["directory"])

    @property
    def supported_audio(self) -> tuple[str, ...]:
        return tuple(self.data["audio"]["supported_formats"])
