"""
Punto de entrada principal del proyecto.

Este módulo existe para facilitar la ejecución desde:

    - Visual Studio Code
    - Línea de comandos
    - Scripts externos

Toda la lógica de ejecución se encuentra en:

    interfaces.cli.app

Por lo tanto este archivo únicamente delega la ejecución
al CLI principal del proyecto.
"""

from interfaces.cli.app_cli import main


if __name__ == "__main__":
    main()
