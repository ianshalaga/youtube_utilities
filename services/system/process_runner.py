# services/system/process_runner.py

import subprocess
from typing import Sequence


class ProcessRunner:
    """
    Ejecuta procesos del sistema de forma consistente.
    Encapsula política de encoding, errores y captura de salida.
    """

    def run(
        self,
        cmd: list[str] | Sequence[str],
        *,
        capture_output: bool = False,
    ) -> subprocess.CompletedProcess:
        """
        Ejecuta un proceso externo de forma consistente y segura.

        - Fuerza UTF-8 para evitar problemas en Windows.
        - Permite captura opcional de salida.
        - Lanza excepción si el proceso falla.

        Args:
            cmd:
                Comando y argumentos.
            capture_output:
                Si True, captura stdout y stderr.

        Returns:
            CompletedProcess
        """
        return subprocess.run(
            cmd,
            check=True,
            capture_output=capture_output,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
