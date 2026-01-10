# Arquitectura del Proyecto youtube_utilities

## 1. Capas del Sistema

### 1.1 Apps (Orquestadores)

Responsables de:

- Coordinar servicios
- Definir flujos
- Manejar paralelización
- Manejar errores globales

Nunca:

- Ejecutan ffmpeg directamente
- Implementan lógica técnica profunda

### 1.2 Domain

Contiene:

- Entidades (Rating, Score, VideoSignature)
- Value Objects
- Reglas del negocio
- Invariantes

No conoce:

- subprocess
- paths del sistema
- herramientas externas

### 1.3 Services

Contiene:

- Runners (MKVMergeRunner)
- Providers (MediaProvider, RankingDataProvider)
- Convertidores (AudioConverter, VideoConverter)

Es infraestructura pura.

### 1.4 Core

Funciones matemáticas puras:

- clamp
- bayesian smoothing
- helpers numéricos

---

## 2. Dominio Multimedia

- MediaProvider define el contrato
- FFProbeProvider implementa ffprobe
- VideoSignature valida compatibilidad
- VideoEncodingDescriptor describe encoding

Conversión y concatenación están separadas por diseño.

---

## 3. Dominio Ranking

Jerarquía:

- Round → Battle → Duel → Ranking

Principios:

- Raw points desde eventos atómicos
- Beating factor mide proporción de éxito
- Lvl factor mide dificultad relativa
- Consistency factor corrige inflación
- Rating es comparable
- Score es acumulativo

---

## 4. Paralelización

Reglas:

- Solo a nivel app
- Cada tarea es autocontenida
- Directorios temporales aislados
- Limpieza garantizada

---

## 5. Decisiones Clave

- End screens generadas desde el mismo video
- No concatenar videos incompatibles jamás
- Providers para desacoplar datos
- Arquitectura preparada para ML futuro
