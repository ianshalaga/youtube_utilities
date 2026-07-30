# services/media/video/mkvmerge_runner.py

import json
import tempfile
from pathlib import Path

from services.system.process_runner import ProcessRunner


class MKVMergeRunner:
    """
    Ejecuta comandos mkvmerge.

    Esta clase no contiene lógica de dominio ni reglas de negocio.
    Su única responsabilidad es ejecutar mkvmerge de forma segura.
    """

    def __init__(self, process_runner: ProcessRunner):
        self._runner = process_runner

    def run(self, cmd: list[str]) -> None:
        """
        Ejecuta un comando mkvmerge.

        Args:
            cmd:
                Lista de argumentos del comando mkvmerge.

        Raises:
            subprocess.CalledProcessError:
                Si mkvmerge falla.
        """
        executable = cmd[0]
        arguments = cmd[1:]

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            delete=False,
        ) as f:
            json.dump(arguments, f, ensure_ascii=False)

            args_file = Path(f.name)

        try:
            self._runner.run([
                executable,
                f"@{args_file}"
            ], capture_output=True)
        finally:
            args_file.unlink(missing_ok=True)
