# youtube_utilities — Documento Maestro del Proyecto

## 1. Visión General

**youtube_utilities** es un proyecto modular orientado a la automatización,
procesamiento y análisis de contenido multimedia (audio, video) y datos
competitivos (ranking), diseñado con una arquitectura extensible y mantenible.

El proyecto no es un conjunto de scripts aislados, sino un **ecosistema de apps**
que comparten principios arquitectónicos, servicios reutilizables y modelos de dominio.

---

## 2. Filosofía del Proyecto

Principios rectores:

- Separación estricta de responsabilidades
- Orquestadores sin lógica técnica pesada
- Servicios pequeños, explícitos y reutilizables
- Dominio desacoplado de infraestructura
- Validación temprana (fail fast)
- Paralelización segura solo a nivel orquestador

El objetivo es **evolución sin reescritura**.

---

## 3. Apps Actuales

### 3.1 video_music

Genera videos musicales a partir de un video base y múltiples pistas de audio.

Características:

- Conversión de audio con normalización
- Corte y muxeo con mkvmerge
- Paralelización por pista
- Salida particionada en subdirectorios

### 3.2 video_joiner

Une múltiples videos compatibles en uno o más archivos finales.

Características:

- Validación estricta de compatibilidad
- Particionado equilibrado por duración
- Generación automática de timestamps
- End screens generadas sin romper compatibilidad
- Ejecución paralela por parte

### 3.3 ranking_system (en desarrollo)

Motor de ranking competitivo basado en battles y duels.

Características:

- Sistema jerárquico de puntuación
- Factores de nivel (lvl_factor)
- Suavizado bayesiano
- Rating, Score y Consistency Factor
- Múltiples vistas de ranking (global, torneo, país, single-player)

---

## 4. Estructura General del Proyecto

- apps/: Casos de uso / orquestadores
- domain/: Modelos de dominio y reglas
- services/: Infraestructura y servicios reutilizables
- core/: Utilidades matemáticas y helpers puros

---

## 5. Estado Actual

El proyecto se encuentra en una fase avanzada de diseño e implementación,
con foco reciente en:

- Consolidación del sistema de ranking
- Refinamiento de abstracciones multimedia
- Eliminación de acoplamientos implícitos
- Preparación para extensiones futuras (ML, dashboards, APIs)
