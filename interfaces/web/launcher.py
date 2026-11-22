"""
Launcher para el servidor web de YouTube Utilities.

Configura el entorno de Django, arranca el servidor HTTP local
y abre automáticamente la aplicación en el navegador predeterminado.
"""

import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

import django


def wait_for_server(host: str, port: int, timeout: float = 5.0) -> bool:
    """Espera activamente a que el servidor web comience a aceptar conexiones."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.1):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.05)
    return False


def open_browser_when_ready(url: str, host: str, port: int, timeout: float = 5.0) -> None:
    """Espera a que el servidor esté listo y abre la URL en el navegador."""
    wait_for_server(host, port, timeout=timeout)
    webbrowser.open(url)


def setup_django_environment() -> None:
    """Configura las rutas del sistema y los ajustes de Django."""
    project_root = Path(__file__).resolve().parents[2]
    web_root = Path(__file__).resolve().parent

    if str(web_root) not in sys.path:
        sys.path.insert(0, str(web_root))
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    django.setup()


def launch_web_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    *,
    open_browser: bool = True,
    browser_timeout: float = 5.0,
) -> None:
    """
    Inicializa el entorno Django y arranca el servidor web.

    Args:
        host: Dirección IP o interfaz de enlace.
        port: Puerto TCP donde escuchará el servidor.
        open_browser: Si es True, abre la aplicación en el navegador predeterminado.
        browser_timeout: Segundos máximos de espera antes de abrir el navegador.
    """
    setup_django_environment()

    from django.core.management import call_command

    url = f"http://localhost:{port}"

    if open_browser:
        thread = threading.Thread(
            target=open_browser_when_ready,
            args=(url, host, port, browser_timeout),
            daemon=True,
        )
        thread.start()

    addrport = f"{host}:{port}"
    call_command("runserver", addrport, use_reloader=False)
