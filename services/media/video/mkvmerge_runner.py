import subprocess


class MKVMergeRunner:
    """
    Ejecuta comandos mkvmerge.

    Esta clase no contiene lógica de dominio ni reglas de negocio.
    Su única responsabilidad es ejecutar mkvmerge de forma segura.
    """

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
        subprocess.run(cmd, check=True)
