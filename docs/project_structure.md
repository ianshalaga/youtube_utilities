# Estructura del proyecto

Este documento describe la organización observada en el repositorio y señala los puntos de entrada principales. No todas las carpetas bajo `applications/` están integradas en CLI o Django; cada flujo debe rastrearse hasta su interfaz antes de modificarlo.

## Vista general

```text
.
├── app.py
├── applications/
├── composition/
├── config/
├── core/
├── data/
├── docs/
├── domain/
├── interfaces/
│   ├── cli/
│   └── web/
├── services/
├── static/
├── tests/
└── tools/
```

En la raíz también hay archivos de configuración y datos locales, como `config.json`, manifiestos, `requirements.txt` y bases SQLite. No son módulos de código fuente.

## Código de aplicación

### `applications/`

Contiene casos de uso y herramientas organizadas por área:

- `video_music/`: procesamiento de video musical y sus entradas, resultados y progreso.
- `video_joiner/`: unión y particionado de videos.
- `youtube_video_manager/`: coordinación del flujo de gestión de vídeos de YouTube.
- `ranking_system/`: loaders, consultas, resolvers y acceso de aplicación al sistema de ranking.
- `youtube_saga_analysis/`, `game_analysis/`, `psn_optimizer/`: análisis y utilidades específicas.
- `overlays/`, `autohotkey_apps/`: recursos web y scripts auxiliares.

La presencia de un módulo aquí no garantiza que tenga un punto de entrada en la CLI o en la web.

### `domain/`

Modelos y reglas agrupados por dominio:

- `youtube/`: vídeos, metadatos, álbumes, manifiestos, operaciones, trabajos y contratos.
- `ranking/`: entidades, eventos, estadísticas, puntuación y motor de ranking.
- `media/`: modelos de audio y video, incluyendo firmas y parámetros de codificación.

### `services/`

Capacidades técnicas, integraciones y persistencia:

- `media/`: conversión, inspección de medios y ejecución de `mkvmerge`.
- `youtube/`: API, discovery, planificación, actualización, manifiestos y persistencia SQLAlchemy.
- `ranking/`: almacenamiento y consultas de ranking.
- `filesystem/`: operaciones de sistema de archivos.
- `system/`: ejecución de procesos externos.
- `scraping/`: automatización de navegador, scraping y consultas auxiliares.

### `composition/`

Ensamblaje de dependencias de casos de uso. Por ejemplo, `video_music.py` construye los servicios multimedia que requiere `VideoMusicProcessor`.

### `core/`

Infraestructura compartida: gestión de configuración, logging, progreso, detección de herramientas, utilidades matemáticas y de tiempo.

## Interfaces

### `interfaces/cli/`

- `app_cli.py`: parser, comandos y coordinación de la ejecución CLI.
- `builders/`: construcción de entradas desde la interacción de consola.
- `presenters/`: presentación de resultados.

El punto de entrada del repositorio, `app.py`, delega en `interfaces.cli.app_cli.main`.

### `interfaces/web/`

Proyecto Django independiente con configuración en `config/`, comando de gestión en `manage.py`, aplicaciones Django en `apps/`, funcionalidades compartidas en `features/`, templates y recursos estáticos. Sus rutas principales enlazan inicio, video musical, unión de video, conversión de audio y explorador de archivos.

Los recursos de frontend se dividen entre `static_src/` (fuentes) y `static/` (recursos servidos). La configuración de Tailwind está en `package.json` y `package-lock.json` dentro de esta interfaz.

## Configuración y datos

- `config.json`: configuración general leída por `core/config_manager.py`.
- `config/youtube/album_manifest.yaml`: manifiesto de entrada para el gestor de YouTube.
- `data/`: datos del proyecto.
- `yvm.db`, `sse.db`: bases SQLite presentes en la raíz; la sesión de YouTube declara `yvm.db` y ranking tiene su propio módulo de sesión.
- `static/`: recursos estáticos de nivel raíz, distintos de `interfaces/web/static/`.

Antes de mover o reemplazar bases locales, verificar sus consumidores y estado; pueden contener datos de usuario.

## Pruebas y herramientas

- `tests/`: pruebas organizadas por dominio, servicios, aplicaciones, composición, interfaces e integración; `tests/manual/` contiene comprobaciones manuales.
- `tools/`: scripts para inspeccionar la estructura y exportar contexto del proyecto.
- `docs/`: documentación general y documentos específicos de ranking y del gestor de YouTube.

## Puntos de entrada comprobados

| Flujo | Entrada | Implementación principal |
|---|---|---|
| CLI | `app.py` → `interfaces/cli/app_cli.py` | Comandos registrados en `build_parser()` y `main()` |
| Web | `interfaces/web/manage.py` | Proyecto Django configurado en `interfaces/web/config/` |
| Video musical CLI | Comando `video_music` | `applications/video_music/` con composición en `composition/video_music.py` |
| Unión de video CLI | Comando `video_joiner` | `applications/video_joiner/` y `services/media/video/` |
| Gestor YouTube CLI | Comando `youtube_video_manager` | `applications/youtube_video_manager/` y `services/youtube/` |

Para saber si otra aplicación está disponible, revisar el parser y el mapa de comandos de la CLI, las rutas Django y sus `INSTALLED_APPS`; no deducirlo únicamente por el nombre de la carpeta.

