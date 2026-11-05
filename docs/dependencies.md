# Dependencias

Este documento resume las dependencias declaradas y las herramientas externas usadas por el repositorio. Las versiones exactas instaladas pueden diferir de los manifiestos; no se han inferido versiones fijadas cuando el proyecto no las especifica.

## Python

El manifiesto común es `requirements.txt`:

| Paquete | Declaración | Uso principal observado |
|---|---|---|
| Django | Sin versión fijada | Proyecto web en `interfaces/web/` |
| SQLAlchemy | `>=2.0` | Persistencia de YouTube y ranking |
| PyYAML | Sin versión fijada | Lectura del manifiesto YAML de YouTube |
| Rich | Sin versión fijada | Presentación de salida en CLI |
| google-api-python-client | Sin versión fijada | Cliente de YouTube Data API |
| google-auth-oauthlib | Sin versión fijada | Flujo OAuth del cliente de YouTube |
| google-auth-httplib2 | Sin versión fijada | Transporte HTTP de autenticación de Google |
| pytest | Sin versión fijada | Ejecución de pruebas |
| pytest-django | Sin versión fijada | Integración de pytest con Django |
| djlint | Sin versión fijada | Herramienta de lint/format para templates Django |

El repositorio no declara un archivo de bloqueo Python ni fija una versión mínima de Python en `pyproject.toml`. El archivo `pyproject.toml` actual configura `djlint`; no define metadatos de paquete ni dependencias.

## Frontend de la interfaz web

`interfaces/web/package.json` declara como dependencias de desarrollo:

- `tailwindcss` (`^4.3.3`)
- `@tailwindcss/cli` (`^4.3.3`)

`npm run css:build` genera `static/css/main.css` a partir de `static_src/css/main.css`. `npm run css:watch` vigila esa entrada durante el desarrollo. El detalle de versiones resueltas está en `interfaces/web/package-lock.json`.

El script npm llamado `test` es solo un placeholder que finaliza con error; no representa una suite de frontend configurada.

## Herramientas multimedia externas

Estas herramientas se instalan fuera de Python y se ejecutan como procesos del sistema:

| Herramienta | Uso | Configuración observada |
|---|---|---|
| FFmpeg (`ffmpeg`) | Conversión de audio y video | Ruta `paths.ffmpeg` en `config.json` |
| FFprobe (`ffprobe`) | Lectura de duración y metadatos multimedia | Ruta `paths.probe` en `config.json` |
| MKVToolNix (`mkvmerge`) | Muxeo, unión y particionado de contenedores Matroska | Ruta `paths.mkvmerge` en `config.json` |

Son necesarias para los flujos multimedia que las invocan, no para importar o ejecutar todas las demás aplicaciones. Revisar las rutas de la configuración local y la disponibilidad de los ejecutables en Windows antes de diagnosticar errores de proceso.

## Autenticación y archivos de configuración

El gestor de YouTube utiliza OAuth mediante los paquetes de Google indicados arriba. `config.json` apunta a los archivos de credenciales de cliente y token; el manifiesto del álbum se mantiene por separado en `config/youtube/album_manifest.yaml`. Los secretos y tokens son archivos locales de configuración/credenciales, no dependencias que deban compartirse.

## Herramientas de desarrollo y pruebas

- `pytest.ini` configura el proyecto para pytest y registra los marcadores `integration` y `real_youtube`.
- Las pruebas Django utilizan `pytest-django` y `DJANGO_SETTINGS_MODULE=config.settings` según esa configuración.
- `djlint` está configurado en `pyproject.toml` con perfil Django e indentación de cuatro espacios.
- Node.js/npm se requieren para los scripts CSS del frontend, no para los comandos Python de CLI.

## Instalación y cambios

Instalar las dependencias Python desde la raíz con:

```powershell
python -m pip install -r requirements.txt
```

Para las herramientas CSS:

```powershell
cd interfaces/web
npm install
npm run css:build
```

Al agregar una dependencia, actualizar el manifiesto correspondiente (`requirements.txt` o `interfaces/web/package.json`) y explicar qué módulo la necesita. No añadir aquí herramientas del sistema como si fueran paquetes Python.

