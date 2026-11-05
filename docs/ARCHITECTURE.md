# Arquitectura del proyecto

## Propósito y alcance

Este documento describe la estructura que existe actualmente en el repositorio. Las reglas arquitectónicas son objetivos de diseño; los flujos y componentes de las secciones siguientes se han contrastado con el código. Las aplicaciones auxiliares no necesariamente siguen todas las mismas capas.

`youtube_utilities` es una colección de herramientas locales en Python. Incluye procesamiento multimedia, gestión de vídeos de YouTube, ranking y utilidades auxiliares. Tiene una interfaz de línea de comandos y un proyecto web Django separado.

## Mapa del repositorio

```text
app.py                         Entrada Python, delega en la CLI
applications/                  Casos de uso y herramientas de aplicación
composition/                   Construcción de dependencias para casos concretos
config/                        Configuración JSON y manifiestos YAML
core/                          Configuración y utilidades compartidas
domain/                        Modelos y reglas del dominio
interfaces/cli/                Parser, coordinación de comandos y presentación CLI
interfaces/web/                Proyecto Django, vistas, templates y estáticos
services/                      Integraciones, persistencia y capacidades técnicas
tests/                         Pruebas unitarias, integración y manuales
docs/                          Documentación técnica y específica de aplicaciones
```

Otras carpetas bajo `applications/` contienen proyectos auxiliares (por ejemplo overlays, análisis de juegos y herramientas de ranking). No todas están conectadas a la CLI o a la web.

## Capas y dependencias

### `domain/`

Contiene conceptos y reglas del problema independientes de herramientas externas. Por ejemplo, `domain/youtube/` modela vídeos, álbumes, trabajos, operaciones, metadatos y contratos de repositorio. Los modelos de dominio no deberían depender de Django, SQLAlchemy, Google APIs ni procesos del sistema.

### `applications/`

Coordina casos de uso y define sus flujos. Los procesadores multimedia y `YouTubeVideoManagerProcessor` son puntos de orquestación. La capa de aplicación puede depender de dominio y servicios mediante dependencias entregadas desde la composición o la interfaz.

### `services/`

Implementa capacidades técnicas e integraciones: procesos del sistema, conversión y análisis de medios, almacenamiento, scraping, ranking y acceso a YouTube. La persistencia del gestor de YouTube está en `services/youtube/storage/`; la persistencia de ranking está separada en `services/ranking/`.

### `core/`

Agrupa infraestructura transversal del proyecto, como configuración, logging, progreso, detección de herramientas, utilidades de tiempo y matemática. Evitar añadir aquí reglas específicas de una aplicación.

### `composition/`

Construye grafos de dependencias. `composition/video_music.py` conecta `ProcessRunner`, convertidores, proveedores multimedia y `VideoMusicProcessor`. Las interfaces también pueden realizar composición cuando el flujo es local a una entrada concreta.

### `interfaces/`

Convierte argumentos o solicitudes externas en llamadas a casos de uso y presenta sus resultados. No debería absorber lógica de negocio ni detalles de integración que pertenecen a servicios.

Dirección de dependencia recomendada:

```text
interfaces → applications → domain
                   ↓
                services
composition → conecta implementaciones y dependencias
```

La estructura es modular y está inspirada en arquitectura por capas; no es una separación hexagonal uniforme en todos los módulos. Al cambiar un componente, seguir primero las convenciones de su área.

## Puntos de entrada y ejecución

### CLI

`app.py` importa y ejecuta `interfaces.cli.app_cli.main`. La CLI crea `ConfigManager`, analiza un comando y delega a funciones de ejecución. Los comandos registrados incluyen `video_music`, `video_joiner`, `video_converter`, `create_db`, `load_legacy`, `ranking` y `youtube_video_manager`.

La CLI es también responsable de ensamblar dependencias en algunos flujos. Para video musical delega la construcción a `VideoMusicProcessorFactory`; para el gestor de YouTube crea cliente, acceso a datos, servicios y procesador antes de ejecutar el manifiesto.

### Aplicación web

`interfaces/web/manage.py` inicia Django usando `config.settings`. Las rutas de `interfaces/web/config/urls.py` conectan las aplicaciones web de inicio, video musical, unión de video, conversión de audio y explorador de archivos. Las apps web adaptan solicitudes a sus servicios o procesadores y exponen templates y recursos estáticos.

La web y la CLI son interfaces distintas; la presencia de una aplicación en una interfaz no implica que esté disponible en la otra.

## Flujos principales

### Video musical

La CLI crea entradas con `interfaces/cli/builders/video_music_input_builder.py`, obtiene el procesador desde `VideoMusicProcessorFactory` y presenta el resultado con `VideoMusicResultPresenter`. La aplicación coordina las pistas y usa servicios para inspección, conversión de audio y muxeo con herramientas externas. La interfaz web tiene vistas y componentes de progreso propios para ejecutar el trabajo en segundo plano y consultar su estado.

### Unión y conversión de video

`VideoJoinerProcessor` orquesta la unión y partición. Los servicios de medios validan compatibilidad, consultan metadatos y ejecutan herramientas como MKVToolNix/FFmpeg a través de servicios de sistema. La conversión de video usa `VideoConverter` y un proveedor de inspección.

### Gestor de vídeos de YouTube

La CLI ensambla `YouTubeClient` y `YouTubeMethods`, `YouTubeDiscovery`, el lector y constructor de álbum, `OperationsBuilder`/`Planner`, `Updater` y `YouTubeJobRepository`. El procesador lee el manifiesto, descubre los vídeos correspondientes, planifica un trabajo y lo ejecuta; puede continuar un trabajo pendiente o pedir una decisión para un trabajo fallido.

Los modelos y estados pertenecen a `domain/youtube/`. SQLAlchemy y los modelos relacionales residen en `services/youtube/storage/`; la sesión configura una base SQLite llamada `yvm.db`. El repositorio transforma los trabajos entre el dominio y la persistencia. El acceso a la API de Google se encapsula en `services/youtube/api/`.

La implementación actual se centra en planificar y ejecutar las operaciones definidas por el código y el manifiesto. No asumir soporte para capacidades de YouTube que no estén implementadas explícitamente.

### Ranking

La aplicación de ranking contiene loaders, consultas, resolvers y creación de base de datos. Sus servicios de almacenamiento están en `services/ranking/`. Mantener esta persistencia separada de la base del gestor de YouTube.

## Configuración y dependencias externas

- `config.json` proporciona configuración de la aplicación a través de `core/config_manager.py`.
- `config/youtube/album_manifest.yaml` es un manifiesto de entrada del gestor de YouTube.
- FFmpeg/FFprobe y MKVToolNix se invocan como procesos externos para tareas multimedia.
- Django sirve la interfaz web; SQLAlchemy modela persistencia del gestor de YouTube y ranking.
- La integración de YouTube utiliza las bibliotecas de Google enumeradas en `requirements.txt`.

Los archivos SQLite en la raíz son datos locales del proyecto. No tratarlos como documentación ni sobrescribirlos durante cambios arquitectónicos.

## Pruebas

`tests/` refleja la separación por capas: hay pruebas de dominio, servicios, aplicaciones, composición e interfaces, además de pruebas de integración y manuales. Las pruebas de integración que se conectan con servicios reales deben identificarse como tales y no confundirse con pruebas locales aisladas.

Al documentar o modificar un flujo, verificar las implementaciones y pruebas de ese flujo. Este documento no declara que las pruebas se hayan ejecutado.

## Guía para cambios arquitectónicos

1. Localizar el caso de uso, su punto de entrada y las pruebas existentes antes de modificarlo.
2. Reutilizar servicios existentes y conservar las fronteras entre dominio, aplicación, infraestructura e interfaz.
3. Mantener las dependencias externas detrás de servicios o adaptadores cuando el área ya siga ese patrón.
4. No mover persistencia entre aplicaciones sin revisar quién es dueño de los datos y cómo se crean las sesiones.
5. Actualizar esta documentación cuando cambien las capas, los puntos de entrada o los flujos descritos.
