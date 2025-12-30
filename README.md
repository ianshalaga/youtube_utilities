# youtube_utilities

## Descripción general

**YouTube Utilities** es una aplicación local desarrollada en Python que proporciona herramientas de procesamiento multimedia mediante una interfaz gráfica accesible desde el navegador.

Actualmente incluye una aplicación principal orientada a:

- Crear **videos musicales por lote**
- A partir de un **video base** y múltiples **archivos de audio**
- Con conversión, normalización y sincronización automática
- Utilizando **ffmpeg** y **mkvmerge** vía línea de comandos

El proyecto está diseñado para ser **extensible**, permitiendo añadir nuevas aplicaciones multimedia dentro de la misma plataforma (por ejemplo, división de videos en partes).

---

## Características principales

### Procesamiento de audio → video

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
- Python 3.10 o superior

### Herramientas externas

Debe estar instalado al menos uno de los siguientes métodos:

- `ffmpeg`
- `mkvmerge` (MKVToolNix)

El programa intentará detectarlos automáticamente en:

- PATH del sistema
- Rutas estándar de instalación

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/media-tools.git
cd media-tools
```

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
