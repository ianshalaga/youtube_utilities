# youtube_utilities

[toc]

## Descripción general

**YouTube Utilities** es una aplicación local desarrollada en **Python** que proporciona herramientas de procesamiento multimedia mediante una interfaz gráfica accesible desde el navegador.

Actualmente incluye una aplicación principal orientada a:

- Crear **videos musicales por lote**.
- A partir de un **video base** y múltiples **archivos de audio**.
- Con conversión, normalización y sincronización automática.
- Utilizando **ffmpeg** y **mkvmerge** vía línea de comandos.

El proyecto está diseñado para ser **extensible**, permitiendo añadir nuevas aplicaciones multimedia dentro de la misma plataforma (por ejemplo, división de videos en partes).

---

## Características principales

### Procesamiento de audio para el video

- Soporte de audio:

  - MP3
  - FLAC
  - WAV
  - AAC

- Conversión automática del audio **solo para el video**:

  - 48 kHz
  - 320 kbps

- Normalización por sonoridad (LUFS) configurable
- Los archivos originales **no se modifican**

### Video

- Uso de un video base
- Corte exacto del video según la duración real de cada canción
- Eliminación automática de segmentos sobrantes generados por mkvmerge
- Renombrado limpio del archivo final

### Interfaz gráfica

- GUI accesible desde navegador (Chrome / Brave / Edge)
- Selector de archivos y carpetas **nativo de Windows** (tkinter)
- Visualización de logs en tiempo real
- Barra de progreso global

### Robustez

- Detección automática de:

  - `ffmpeg`
  - `mkvmerge`

- Configuración persistente en archivo JSON
- Modo **dry run** (simulación completa sin ejecutar comandos)

---

## Requisitos

### Sistema

- Windows 10 / 11
- [Python](https://www.python.org/downloads/) 3.10 o superior.

### Herramientas externas

Debe estar instalado al menos uno de los siguientes métodos:

- `ffmpeg` (ffmpeg)
- `ffprove` (ffmpeg)
- `mkvmerge` (MKVToolNix)

El programa intentará detectarlos automáticamente en:

- PATH del sistema
- Rutas estándar de instalación

### Obtención de herramientas externas

#### 1. `ffmpeg` (compilaciones listas para Windows)

La página oficial de `ffmpeg` no distribuye ejecutables directamente, pero desde ahí se enlazan builds confiables preparados por terceros autorizados para uso general en Windows.

Opciones de descarga recomendadas:

##### a. Builds de gyan.dev (recomendado para la mayoría de usuarios)

Esta fuente ofrece paquetes con los ejecutables `ffmpeg.exe`, `ffprobe.exe` y `ffplay.exe` ya compilados para Windows:

- [ffmpeg builds gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
- Eligir la versión **release-full** para máxima compatibilidad.
- Descargar y extraer el contenido de la carpeta, por ejemplo en `C:/ffmpeg/`.
- Luego, agregar `C:/ffmpeg/bin` al PATH del sistema para que Python/Flask los reconozca.

##### b. Builds de BtbN (alternativa bastante usada)

También puedes descargar ejecutables estáticos desde el repositorio de compilaciones automáticas (binarios de ejemplo).

- [ffmpeg builds BtbN](https://github.com/btbn/ffmpeg-builds/releases)

##### c. Instalación en Windows

- Descargar el archivo **.7z** o **.zip** desde **gyan.dev** o **BtbN**.
- Extraer la carpeta (usualmente contiene `bin/ffmpeg.exe`, `bin/ffprobe.exe`).
- Renombrar la carpeta extraída como **ffmpeg** y moverla a la ruta `C:/ffmpeg/`.
- Añadir la ruta completa de esa carpeta `bin` (`C:/ffmpeg/bin`) al **PATH** en las **Variables de entorno** de Windows.
- Abrir una terminal y verificar con:

```bash
ffmpeg -version
ffprobe -version
```

#### 2. **MKVToolNix** (incluye `mkvmerge`)

**MKVToolNix** es la suite oficial de herramientas para Matroska (MKV), la cual incluye `mkvmerge`, `mkvinfo`, `mkvextract` y más.

- [MKVToolNix](https://mkvtoolnix.download/)
- Sección **Downloads**.
- Seleccionar el instalador de Windows (32/64 bit) o una versión portátil.
- También está disponible en repositorios como [Fosshub](https://www.fosshub.com/MKVToolNix.html).
- Instalar normalmente (aceptar permisos).
- Asegurarse de que la instalación incluya los ejecutables de CLI (mkvmerge.exe, etc.).
- Agregar la carpeta de instalación de **MKVToolNix** `C:/Program Files/MKVToolNix` al **PATH**.
- Abrir una terminal y verificar con:

```bash
mkvmerge.exe --version
```

#### 3. Cómo agregar `ffmpeg` y `mkvmerge` a la variable de entorno `PATH`

##### 1. Abrir las Variables de Entorno

- Presionar Win + R
- Escribir: `sysdm.cpl`
- Pulsar `Enter`.
- Ir a la pestaña **Opciones avanzadas**.
- Hacer clic en **Variables de entorno…**

##### 2. Elegir qué PATH modificar

Hay dos secciones:

- Variables de usuario → solo afecta a tu usuario.
- Variables del sistema → afecta a todos los usuarios (requiere permisos de administrador).

Recomendación: usar **Variables de usuario** salvo que se necesite acceso global.

##### 3. Editar la variable PATH

- En la sección elegida, buscar **Path**.
- Selecciónarla y hacer clic en **Editar…**
- Aparecerá una lista de rutas existentes.

##### 4. Añadir la nueva ruta

- Hacer clic en **Nuevo**.
- Escribir o pegar la ruta del ejecutable (ejemplo):
  - `C:/ffmpeg/bin`
  - `C:/Program Files/MKVToolNix`
- Agregar una ruta a la vez.
- No incluir el nombre del ejecutable (`ffmpeg.exe`, `mkvmerge.exe`). Solo la carpeta que los contiene.

##### 5. Guardar cambios

- Pulsar **Aceptar** en todas las ventanas abiertas.

##### 6. Verificación

- Cerrar todas las ventanas de **Terminal** abiertas.
- Abrir una nueva **Terminal**.
- Ejecutar:

```bash
ffmpeg -version
mkvmerge --version
```

- Si se muestra la información de versión, el PATH está correctamente configurado.

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/ianshalaga/youtube_utilities.git
cd youtube_utilities
```

- [Git para Windows](https://git-scm.com/install/windows)

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## Ejecución

```bash
python app.py
```

Abrir en el navegador:

`http://localhost:5000`

---

## Estructura del proyecto

```text
media_tools/
│
├── app.py                # Punto de entrada
├── requirements.txt
├── README.md
├── config.json           # Configuración persistente
│
├── core/                 # Infraestructura compartida
│   ├── config_manager.py
│   ├── logger.py
│   ├── progress.py
│   └── tool_detector.py
│
├── services/             # Servicios reutilizables
│   ├── audio/
│   │   ├── converter.py
│   │   └── duration_probe.py
│   └── video/
│       └── mkvmerge_runner.py
│
├── apps/                 # Aplicaciones funcionales
│   └── video_music/
│       ├── routes.py
│       ├── processor.py
│       └── templates/
│           └── video_music.html
│
├── gui/
│   └── file_dialog.py
│
├── static/
│   ├── css/
│   └── js/
│
└── output/               # Videos generados
```

---

## Configuración (`config.json`)

Ejemplo de configuración:

```json
{
  "dry_run": false,
  "max_workers": 4,
  "normalize_audio": true,
  "lufs_target": -14,
  "true_peak": -1.0,
  "lra": 11,
  "ffmpeg_path": "",
  "mkvmerge_path": ""
}
```

### Parámetros clave

| Parámetro         | Descripción                             |
| ----------------- | --------------------------------------- |
| `dry_run`         | Simula el proceso sin ejecutar comandos |
| `max_workers`     | Paralelización del procesamiento        |
| `normalize_audio` | Activa normalización LUFS               |
| `lufs_target`     | Nivel objetivo de sonoridad             |
| `true_peak`       | Pico máximo permitido                   |
| `ffmpeg_path`     | Ruta manual (opcional)                  |
| `mkvmerge_path`   | Ruta manual (opcional)                  |

---

## Modo Dry Run

El modo **dry run** permite:

- Validar archivos y rutas
- Calcular duraciones reales
- Construir los comandos ffmpeg / mkvmerge
- Ver el flujo completo en los logs

Sin:

- Crear archivos
- Ejecutar conversiones
- Modificar el sistema

Ideal para verificar configuraciones antes de ejecutar un batch largo.

---

## Logs

- Logs visibles en la interfaz web
- Exportación automática a archivo de texto
- Cada ejecución queda registrada

---

## Extensibilidad

El proyecto está preparado para:

- Añadir nuevas apps multimedia
- Reutilizar servicios comunes
- Compartir infraestructura (configuración, logging, detección de herramientas)

Ejemplo futuro:

- División de videos
- Reempaquetado
- Conversión por lotes

---

## Limitaciones conocidas

- No se gestiona pausa, cancelación ni reanudación de tareas
- La ejecución batch es directa y continua
- Pensado para uso local (no servidor remoto)

---

## Licencia

Uso personal o interno.
Revisa o define una licencia específica según tus necesidades.

---

## Notas finales

Este proyecto está diseñado como una **herramienta de escritorio moderna**, con backend Python y frontend web, priorizando:

- Claridad
- Robustez
- Extensibilidad
- Flujo de trabajo profesional

---
