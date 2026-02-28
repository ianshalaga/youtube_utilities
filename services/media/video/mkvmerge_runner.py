# services/media/video/mkvmerge_runner.py

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
        self._runner.run(cmd)
