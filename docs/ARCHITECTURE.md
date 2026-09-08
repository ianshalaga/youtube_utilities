# Arquitectura del Proyecto — youtube_utilities

## 1. Propósito

Este documento define la arquitectura vigente del proyecto `youtube_utilities`.

El proyecto aplica una arquitectura por capas inspirada en Clean Architecture,
arquitectura hexagonal y diseño orientado a dominio ligero.

Principios fundamentales:

- Separación estricta de responsabilidades.
- Preferencia por composición sobre herencia.
- Orquestadores sin lógica técnica profunda.
- Servicios pequeños, explícitos y testeables.
- Infraestructura desacoplada del dominio.
- Ausencia de estado global implícito.
- Efectos secundarios explícitos.
- Validación temprana.
- Persistencia aislada por aplicación cuando el estado pertenece a un caso de uso.
- El dominio no conoce APIs, SDKs, sistema operativo ni herramientas externas.

---

## 2. Estructura de capas

### 2.1 Applications

Ubicación:

```text
applications/
```

Las aplicaciones son **orquestadores de casos de uso**.

Responsabilidades:

- Coordinar servicios.
- Definir el flujo de ejecución.
- Conocer el contexto global del caso de uso.
- Gestionar errores a nivel de proceso.
- Decidir qué operaciones se ejecutan y en qué orden.
- Gestionar reanudación, planificación y estado cuando formen parte del caso de uso.

No deben:

- Implementar lógica técnica profunda.
- Ejecutar directamente herramientas externas.
- Construir peticiones HTTP de infraestructura.
- Contener modelos de persistencia.
- Duplicar servicios existentes.

Una aplicación puede tener un `Processor` como punto principal de entrada.

Ejemplos existentes:

- `VideoJoinerProcessor`
- `VideoMusicProcessor`
- `RankingSystemProcessor`

Nueva aplicación prevista:

```text
applications/
└── youtube_video_manager/
```

---

### 2.2 Domain

Ubicación:

```text
domain/
```

El dominio contiene conceptos y reglas que pertenecen al problema, no a una
tecnología concreta.

Puede contener:

- Entidades.
- Value Objects.
- Invariantes.
- Reglas de negocio.
- Modelos de estado.
- Contratos de dominio cuando sean necesarios para desacoplar infraestructura.

No conoce:

- `subprocess`.
- Paths del sistema.
- SQLite.
- HTTP.
- Google APIs.
- SDKs de terceros.
- ffmpeg, mkvmerge u otras herramientas.

Regla:

> El dominio define qué significa algo; la infraestructura define cómo se
> obtiene o ejecuta.

---

### 2.3 Services

Ubicación:

```text
services/
```

Los servicios contienen infraestructura reutilizable.

Responsabilidades típicas:

- Providers.
- Clients.
- Runners.
- Convertidores.
- Repositorios.
- Persistencia.
- Integraciones externas.

Un servicio:

- Tiene una responsabilidad clara.
- Tiene entradas y salidas explícitas.
- No coordina otros servicios.
- No conoce el flujo global de una aplicación.
- No mantiene estado global.
- Es testeable de forma aislada.

La paralelización pertenece al orquestador, no al servicio.

---

### 2.4 Core

Ubicación:

```text
core/
```

Contiene utilidades transversales y funciones puras que no pertenecen a un
dominio concreto.

Ejemplos:

- Matemática.
- Tiempo.
- Configuración común.
- Logging.
- Progress reporting.
- Detección de herramientas.

No debe convertirse en un contenedor genérico para lógica de aplicaciones.

---

## 3. Regla de decisión: dominio, servicio o aplicación

Antes de crear una clase o función:

### ¿Coordina?

Si decide:

- qué paso ocurre primero;
- qué servicios utilizar;
- cuándo reintentar;
- cuándo detenerse;
- qué operaciones quedan pendientes;

entonces pertenece a una **application/orchestrator**.

### ¿Ejecuta una capacidad técnica?

Si:

- llama a una API;
- consulta SQLite;
- ejecuta ffmpeg;
- lee/escribe archivos;
- realiza una petición HTTP;

entonces pertenece a **services**.

### ¿Representa un concepto o regla del problema?

Si modela:

- una entidad;
- un estado;
- una regla;
- una invariante;
- un Value Object;

entonces pertenece al **domain**.

---

# 4. Aplicación de gestión de vídeos de YouTube

## 4.1 Objetivo

La aplicación `youtube_video_manager` automatiza las operaciones de gestión de
vídeos que están expuestas por las APIs oficiales de YouTube y mantiene un
estado persistente para permitir ejecución parcial y reanudación segura.

Su responsabilidad principal no es "hablar con YouTube", sino **coordinar un
proceso de sincronización entre el estado deseado del canal y el estado
observado en YouTube**.

Flujo conceptual:

```text
YouTube
   │
   ▼
Discovery
   │
   ▼
Local SQLite state
   │
   ▼
Planning
   │
   ▼
Execution
   │
   ├── YouTube Data API
   └── operaciones no disponibles por API → estado explícito
```

---

## 4.2 No separar cada operación en una aplicación

No se crearán aplicaciones independientes como:

```text
youtube_metadata_app
youtube_thumbnail_app
youtube_playlist_app
youtube_publish_app
```

Eso fragmentaría artificialmente un único caso de uso.

La aplicación será:

```text
applications/
└── youtube_video_manager/
```

y tendrá distintos casos de uso internos:

- Discovery.
- Planning.
- Execution.
- Status/reporting.

Las operaciones individuales se modelarán como capacidades/servicios y como
operaciones persistentes, no como aplicaciones independientes.

---

## 4.3 Separación entre planificación y ejecución

El proceso tendrá cuatro etapas conceptuales:

```text
DISCOVER
    ↓
PLAN
    ↓
EXECUTE
    ↓
REPORT
```

### Discovery

Obtiene desde YouTube la información necesaria para identificar los vídeos:

- `video_id`.
- título actual.
- fecha de subida.
- estado de privacidad.
- otros datos necesarios para sincronización.

Los vídeos se ordenarán localmente por fecha de subida, de más antiguo a más
reciente.

### Planning

Determina qué debería cambiar en cada vídeo y crea operaciones pendientes.

Ejemplo:

```text
video ABC

metadata       → pending
thumbnail      → pending
playlist A     → pending
playlist B     → pending
publication    → pending
monetization   → unsupported
end_screen     → unsupported
```

### Execution

Ejecuta únicamente operaciones pendientes que puedan realizarse con la cuota
disponible.

Cada resultado se persiste inmediatamente.

### Reporting

Permite conocer:

- completados;
- pendientes;
- fallidos;
- no soportados;
- cuota consumida;
- última ejecución;
- errores.

---

# 5. Persistencia de YouTube: SQLite independiente

La aplicación de YouTube tendrá **su propia base SQLite**.

No debe utilizar ni modificar la base de datos de `services/ranking/storage`.

Estructura conceptual:

```text
services/
└── youtube_video_manager/
    └── storage/
        ├── models/
        ├── repository.py
        ├── session.py
        └── ...
```

La ubicación exacta podrá ajustarse a las convenciones existentes, pero la
propiedad arquitectónica es obligatoria:

> El estado de gestión de YouTube pertenece a la aplicación de YouTube y no al
> dominio/persistencia del sistema de ranking.

La base debe permitir conservar el estado aunque la aplicación termine
prematuramente.

---

# 6. Modelo de estado y reanudación

No se utilizará un JSON como fuente de verdad para el estado de ejecución.

SQLite será la fuente de verdad.

Cada vídeo podrá tener múltiples operaciones.

Ejemplo:

```text
Video
 ├── metadata       completed
 ├── thumbnail      completed
 ├── playlist A     completed
 ├── playlist B     pending
 ├── publication    pending
 ├── monetization   unsupported
 └── end_screen     unsupported
```

Esto evita considerar un vídeo simplemente como `completed/failed`.

## Estados mínimos

```text
pending
running
completed
failed
unsupported
```

El estado `pending` también debe utilizarse cuando una operación sea válida
pero no haya cuota suficiente.

Agotar la cuota no es un error de la operación.

---

# 7. Idempotencia

La ejecución debe ser reanudable.

Si el proceso se detiene:

```text
video 001 → completed
video 002 → completed
video 003 → completed
video 004 → pending
...
```

una nueva ejecución debe continuar desde `004`.

No se debe volver a ejecutar una operación marcada como `completed` salvo que
una operación explícita de resync lo solicite.

Las operaciones que puedan producir duplicados deben comprobar previamente el
estado remoto cuando sea necesario.

---

# 8. Cuota de YouTube

La cuota se tratará como una dependencia explícita del ejecutor.

No se distribuirán comprobaciones de cuota arbitrarias por el código.

Debe existir un componente responsable de:

- coste estimado de una operación;
- cuota consumida;
- cuota disponible;
- límite diario;
- operaciones que no pueden ejecutarse con la cuota restante.

La cuota no debe modelarse como un número mágico.

A fecha de este documento, la YouTube Data API mantiene una cuota general de
10.000 unidades/día para los métodos del bucket general. Desde junio de 2026,
`videos.insert` y `search.list` utilizan buckets de cuota específicos; el resto
de métodos continúa en el bucket general. La cuota debe considerarse
configuración consultable, no una constante arquitectónica.

---

# 9. Operaciones de YouTube previstas

## 9.1 `videos.update`

Será la operación principal para actualizar:

- título;
- descripción;
- etiquetas;
- categoría;
- idioma;
- privacidad;
- fecha de publicación programada;
- `selfDeclaredMadeForKids`;
- `containsSyntheticMedia`;
- otros campos explícitamente soportados por la API.

La llamada a `videos.update` tiene un coste de 50 unidades.

Importante:

Cuando se actualiza `snippet`, `snippet.categoryId` debe estar incluido.
Asimismo, `publishAt` requiere `privacyStatus=private` y el vídeo debe ser
privado y no haber sido publicado previamente.

La aplicación debe construir solicitudes completas y deliberadas para evitar
el borrado accidental de propiedades mutables no incluidas en una actualización.

---

## 9.2 Miniaturas

Las miniaturas se gestionarán mediante un servicio específico que utilice
`thumbnails.set`.

No forman parte de `videos.update`.

El coste documentado es aproximadamente 50 unidades por llamada y el límite
de archivo es 2 MB.

---

## 9.3 Playlists

Agregar un vídeo a una playlist se modelará como una operación independiente
mediante `playlistItems.insert`.

El coste documentado es 50 unidades por llamada.

La aplicación debe comprobar, cuando corresponda, si el vídeo ya pertenece a
la playlist antes de intentar insertarlo.

---

## 9.4 Programación

La programación se tratará como una operación de publicación y podrá formar
parte del mismo `videos.update` que la metadata.

No debe crearse una segunda llamada `videos.update` innecesariamente si todos
los cambios pueden realizarse de forma segura en una sola actualización.

---

## 9.5 Operaciones no disponibles

La aplicación no debe fingir soporte para funcionalidades que la API pública
no expone.

Por ejemplo, monetización y determinadas configuraciones de YouTube Studio
que no estén expuestas por la Data API deben representarse explícitamente
como:

```text
unsupported
```

Esto no significa que sean imposibles mediante YouTube Studio; significa que
no forman parte de este pipeline basado exclusivamente en la Data API.

Si en el futuro se incorpora otro mecanismo autorizado, se añadirá como una
nueva infraestructura, no como una excepción oculta dentro de `videos.update`.

---

# 10. Providers y clients de YouTube

La infraestructura de YouTube debe desacoplar la aplicación del SDK/API
concreta.

Estructura conceptual:

```text
services/
└── youtube_api/
    ├── client.py
    ├── authentication.py
    ├── channels.py
    ├── videos.py
    ├── playlists.py
    ├── playlist_items.py
    ├── thumbnails.py
    └── quota.py
```

Los nombres son orientativos.

Regla:

```text
Application
    ↓
YouTube service/provider
    ↓
Google API client
    ↓
YouTube
```

La aplicación no debe construir directamente peticiones HTTP a Google.

---

# 11. Discovery de vídeos

Para enumerar los vídeos subidos no se utilizará `search.list` salvo que exista
una razón específica.

YouTube proporciona una playlist especial de vídeos subidos al canal. Su
`playlistId` puede obtenerse desde el recurso del canal y posteriormente
recorrerse con `playlistItems.list`.

Esto permite recuperar `videoId`, título y fecha relevante con un coste muy
bajo y paginación de hasta 50 elementos por solicitud.

El resultado se persistirá en SQLite y se ordenará localmente por fecha de
subida ascendente.

---

# 12. Batching

El concepto de batch de la aplicación no debe confundirse con el batching HTTP
de Google.

La aplicación utilizará un **logical batch**:

```text
UpdateJob
 ├── Operation
 ├── Operation
 ├── Operation
 └── ...
```

Cada operación mantiene su propio estado.

La ejecución puede detenerse por cuota sin convertir todo el job en `failed`.

Si el batching HTTP de Google se utiliza posteriormente, será una optimización
de infraestructura y no el mecanismo de persistencia ni recuperación.

---

# 13. Transacciones y persistencia

El estado debe persistirse de forma que nunca se marque una operación como
`completed` antes de que la llamada remota haya terminado correctamente.

Orden:

```text
pending
   ↓
running
   ↓
API call
   ↓
success
   ↓
completed
```

En caso de excepción:

```text
running
   ↓
failed
```

En caso de cuota insuficiente antes de llamar:

```text
pending
```

No:

```text
failed
```

La transición de estado y los datos necesarios para reanudar deben quedar
persistidos de manera atómica cuando sea posible.

---

# 14. Errores

Deben distinguirse al menos:

- error de autenticación;
- error de autorización;
- recurso inexistente;
- parámetros inválidos;
- conflicto/duplicado;
- cuota insuficiente;
- error temporal de red;
- error permanente de API;
- operación no soportada.

No todos los errores deben provocar el mismo comportamiento.

Ejemplo:

```text
quota exhausted      → pending
temporary network    → retryable/failed
invalid metadata     → failed
unsupported feature  → unsupported
success              → completed
```

---

# 15. Paralelización

La aplicación podrá paralelizar operaciones independientes únicamente cuando
sea seguro hacerlo.

La paralelización debe gestionarse en la application/orchestrator.

Los servicios no deben crear pools de workers ni paralelizar internamente.

La persistencia debe protegerse contra actualizaciones concurrentes del mismo
registro.

En una primera implementación se recomienda ejecución secuencial y correcta.
La paralelización podrá añadirse después de medir su necesidad.

---

# 16. Dominio de YouTube frente al dominio del canal

El concepto:

> "este vídeo pertenece al juego X"

pertenece al dominio del canal, no necesariamente al recurso `video` de la
API de YouTube.

Debe evitarse introducir referencias arbitrarias al sistema de ranking dentro
del modelo de YouTube.

La relación entre vídeo y juego podrá modelarse posteriormente mediante una
entidad/value object propio si se demuestra que es necesaria para generar
metadata, playlists o reglas de publicación.

---

# 17. Testing

Orden recomendado:

1. Tests de dominio.
2. Tests de planificación.
3. Tests de persistencia.
4. Tests de servicios con mocks/fakes.
5. Tests de integración con YouTube.
6. Tests end-to-end.

Se debe poder probar el planificador y el ejecutor sin consumir cuota real.

---

# 18. Evolución

La primera versión debe ser deliberadamente pequeña:

```text
Discovery
   ↓
SQLite
   ↓
videos.update
   ↓
estado persistente
```

Después:

```text
+ thumbnails
+ playlists
+ publication scheduling
+ quota planning
+ reporting
```

Y únicamente después:

```text
+ operaciones adicionales
+ optimización
+ paralelización
```

La arquitectura debe permitir ampliar operaciones sin convertir
`YoutubeVideoManagerProcessor` en una clase monolítica.

---

# 19. Reglas que no deben romperse

1. Una application coordina; un service ejecuta.
2. El dominio no conoce YouTube.
3. La API de Google no debe filtrarse al dominio.
4. La base SQLite de YouTube es independiente de la de ranking.
5. SQLite es la fuente de verdad del estado de ejecución.
6. Cada operación tiene estado propio.
7. Cuota insuficiente significa `pending`, no `failed`.
8. Los cambios completados nunca deben perderse al reanudar.
9. No se debe asumir que YouTube Studio y la Data API ofrecen las mismas
   funcionalidades.
10. Las operaciones no soportadas deben representarse explícitamente.
11. Los servicios no deben paralelizar internamente.
12. Las llamadas API deben estar encapsuladas en servicios de infraestructura.
13. Las decisiones de negocio y planificación pertenecen al orquestador/dominio.
14. No introducir dependencias del ranking para resolver el estado de YouTube.
