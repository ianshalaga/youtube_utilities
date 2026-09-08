# Guía para Desarrolladores — youtube_utilities

## 1. Antes de escribir código

Antes de crear una clase, función o archivo, responde:

1. ¿Esto es dominio, servicio o aplicación?
2. ¿Coordina o ejecuta?
3. ¿Conoce contexto global?
4. ¿Tiene efectos secundarios?
5. ¿Su estado debe persistir?
6. ¿Existe ya una capacidad equivalente en el proyecto?

Regla rápida:

```text
¿Decide qué hacer?
        ↓
    Application

¿Ejecuta una capacidad técnica?
        ↓
      Service

¿Representa una regla o concepto del problema?
        ↓
      Domain
```

---

## 2. Agregar una nueva aplicación

La estructura real del proyecto utiliza:

```text
applications/
```

No `apps/`.

Pasos:

1. Crear la carpeta de la aplicación.
2. Definir su `Processor` o punto de entrada.
3. Identificar los servicios necesarios.
4. Definir el flujo del caso de uso.
5. No duplicar lógica de servicios existentes.
6. Crear tests.
7. Documentar la aplicación cuando su comportamiento lo justifique.

Para la gestión de YouTube:

```text
applications/
└── youtube_video_manager/
```

No crear una aplicación diferente por cada operación de YouTube.

---

## 3. Crear un servicio

Un servicio debe:

- Tener una responsabilidad.
- Tener entradas y salidas explícitas.
- No coordinar otros servicios.
- No mantener estado global.
- Ser reutilizable.
- Ser testeable sin ejecutar necesariamente infraestructura real.

Ejemplo conceptual:

```text
YouTubeVideoService
    update_video_metadata(...)
```

es una capacidad técnica.

En cambio:

```text
YoutubeVideoManagerProcessor
    discover()
    plan()
    execute()
```

coordina el caso de uso.

---

## 4. No introducir lógica técnica en los Processors

Un Processor no debe:

- construir URLs HTTP;
- ejecutar comandos externos;
- abrir conexiones SQLite directamente;
- conocer detalles del SDK de Google;
- implementar algoritmos de retry de bajo nivel.

El Processor decide:

```text
qué
cuándo
en qué orden
qué hacer ante un resultado
```

El servicio decide:

```text
cómo
```

---

## 5. Aplicación YouTube Video Manager

La aplicación seguirá el flujo:

```text
discover
    ↓
plan
    ↓
execute
    ↓
report
```

### Discovery

Obtiene el inventario remoto y lo sincroniza con SQLite.

No debe modificar metadata de YouTube.

### Planning

Convierte el estado deseado en operaciones concretas.

Ejemplo:

```text
Video ABC

UPDATE_METADATA
SET_THUMBNAIL
ADD_TO_PLAYLIST
SCHEDULE_PUBLICATION
```

Las operaciones no soportadas se registran como `unsupported`.

### Execution

Consume operaciones pendientes respetando:

- dependencias;
- estado remoto;
- cuota;
- errores;
- idempotencia.

### Report

No modifica YouTube.

Devuelve un resumen de:

- completed;
- pending;
- failed;
- unsupported;
- quota usage.

---

## 6. SQLite de la aplicación

La base de datos de YouTube debe ser independiente.

No reutilizar:

```text
services/ranking/storage/
```

para almacenar el estado de YouTube.

La aplicación debe disponer de su propia persistencia, siguiendo el patrón de
infraestructura del proyecto:

```text
services/
└── youtube_video_manager/
    └── storage/
```

La base debe registrar como mínimo:

- vídeos descubiertos;
- datos relevantes del vídeo;
- operaciones;
- estado de cada operación;
- timestamps;
- intentos;
- errores;
- información suficiente para reanudar.

---

## 7. Nunca utilizar JSON como fuente de verdad del job

Un JSON puede utilizarse como:

- exportación;
- debugging;
- snapshot;
- intercambio de datos.

No debe utilizarse como mecanismo principal de recuperación.

El estado operativo vive en SQLite.

---

# 8. Idempotencia

Toda operación debe poder determinar si ya se realizó.

Antes de hacer algo que pueda producir duplicación:

```text
¿ya está aplicado?
    ├── sí → completed
    └── no → ejecutar
```

Ejemplo:

```text
Añadir vídeo a playlist

¿video ya está en playlist?
    ├── sí → marcar completed
    └── no → playlistItems.insert
```

No se debe depender exclusivamente de que YouTube devuelva un error para
detectar duplicados.

---

# 9. Cuota

Nunca escribir:

```python
if remaining_quota < 50:
```

repetidamente en diferentes módulos.

Debe existir un componente central de cuota.

El ejecutor debe preguntar:

```text
can_execute(operation)
```

y, si no puede:

```text
operation.status = pending
```

No debe consumir cuota innecesariamente para descubrir que no queda cuota.

Las operaciones que puedan agruparse en una sola llamada deben planificarse
como una sola llamada.

Por ejemplo:

```text
title
description
tags
category
publishAt
```

pueden formar parte de un único `videos.update`.

---

# 10. Estados de operación

Estados recomendados:

```text
pending
running
completed
failed
unsupported
```

Interpretación:

### pending

Todavía debe ejecutarse.

También se utiliza cuando no hay cuota suficiente.

### running

La aplicación ha iniciado la ejecución y todavía no ha recibido un resultado
final.

### completed

La operación remota terminó correctamente o el estado remoto ya coincidía con
el estado deseado.

### failed

La operación no pudo completarse y requiere atención o retry según el tipo de
error.

### unsupported

La capacidad no está expuesta por la infraestructura utilizada.

---

# 11. Errores y retries

No todos los errores se reintentan.

## Retryable

Ejemplos:

- errores temporales de red;
- ciertos errores transitorios de API;
- rate/quota temporal cuando corresponda.

## No retryable automáticamente

Ejemplos:

- metadata inválida;
- playlist inexistente;
- vídeo inexistente;
- autorización insuficiente;
- parámetros incorrectos.

El tipo de error debe quedar registrado.

---

# 12. YouTube Data API

Los servicios de YouTube encapsulan la API.

La application no debe hacer directamente:

```python
youtube.videos().update(...)
```

Debe solicitar al servicio correspondiente una operación semántica.

Ejemplo conceptual:

```text
Processor
    ↓
YouTubeVideoService
    ↓
Google API client
```

Esto permite sustituir el cliente, utilizar mocks y evitar que detalles del SDK
se propaguen por todo el proyecto.

---

# 13. Discovery de vídeos

Para descubrir los vídeos del canal:

1. Obtener la playlist de vídeos subidos.
2. Recorrer `playlistItems.list`.
3. Extraer `videoId`, título y fecha.
4. Persistir/sincronizar en SQLite.
5. Ordenar localmente por fecha de subida ascendente.

No utilizar `search.list` como mecanismo predeterminado para enumerar el canal.

---

# 14. Actualización de metadata

`videos.update` permite actualizar, entre otros:

- título;
- descripción;
- tags;
- categoría;
- idioma;
- privacidad;
- fecha programada;
- declaración `madeForKids`;
- declaración de contenido sintético.

El coste de una llamada es de 50 unidades.

Cuando se modifica `snippet`, incluir explícitamente `categoryId`.

No crear llamadas independientes para cada propiedad si varias pueden actualizarse
de forma segura en una misma llamada.

---

# 15. Miniaturas

Las miniaturas utilizan una operación distinta:

```text
thumbnails.set
```

El servicio debe recibir un archivo válido y realizar la subida.

El coste documentado es aproximadamente 50 unidades.

La miniatura debe modelarse como una operación independiente de metadata.

---

# 16. Playlists

Añadir un vídeo:

```text
playlistItems.insert
```

El coste documentado es 50 unidades.

La aplicación debe evitar duplicados y registrar el resultado individualmente.

---

# 17. Publicación programada

La publicación programada forma parte de `videos.update`.

Regla:

```text
publishAt
    ⇒ privacyStatus = private
```

y el vídeo debe cumplir las condiciones de YouTube para publicación programada.

Si metadata y programación pueden realizarse en una única actualización,
hacerlo en una sola llamada.

---

# 18. Funcionalidades no expuestas por la Data API

No implementar hacks dentro de los servicios de YouTube para simular funciones
de YouTube Studio que no estén expuestas por la API utilizada.

Ejemplo conceptual:

```text
monetization
    → unsupported_by_data_api

end_screen_configuration
    → unsupported_by_data_api

ad_suitability_questionnaire
    → unsupported_by_data_api
```

Si posteriormente se utiliza otro mecanismo autorizado, se añadirá como nueva
infraestructura.

---

# 19. Tests

Prioridad:

```text
Domain
   ↓
Planning
   ↓
Storage
   ↓
Services
   ↓
Integration
   ↓
End-to-end
```

Los tests del planificador deben poder ejecutarse sin cuota real de YouTube.

Los servicios deben poder probarse con fake/mock clients.

---

# 20. Naming

El proyecto prioriza nombres explícitos.

Preferir:

```text
get_uploaded_video_playlist_id
calculate_operation_cost
mark_operation_as_completed
```

sobre:

```text
get_id
cost
done
```

Evitar:

```text
doStuff
processData
handle
manager
helper
utils
```

cuando no expresen claramente la responsabilidad.

---

# 21. Validación temprana

Aplicar:

> Fall early, fail loud.

Validar antes de ejecutar operaciones costosas o irreversibles.

Ejemplos:

- `video_id` válido;
- playlist existente;
- metadata válida;
- fecha de publicación válida;
- archivo de miniatura válido;
- operación compatible con el estado actual.

---

# 22. Paralelización

La primera implementación debe ser secuencial.

Solo paralelizar después de demostrar que es necesario.

Si se paraleliza:

- hacerlo en la application;
- no dentro de services;
- no compartir estado mutable sin protección;
- no ejecutar simultáneamente operaciones dependientes;
- no permitir que dos workers modifiquen la misma operación.

---

# 23. Documentación

Los docstrings deben funcionar como contratos.

No escribir comentarios que simplemente repitan el código.

Documentar:

- precondiciones;
- postcondiciones;
- efectos secundarios;
- excepciones relevantes;
- invariantes;
- costes de API cuando sean relevantes para el comportamiento.

---

# 24. Flujo recomendado de implementación

Para `youtube_video_manager`, implementar en este orden:

### Fase 1 — Arquitectura y modelos

- estructura de paquetes;
- entidades/value objects necesarios;
- modelo de operación;
- estados;
- contratos de repositorio.

### Fase 2 — SQLite

- schema;
- session;
- repositories;
- migraciones si fueran necesarias.

### Fase 3 — Autenticación y client

- OAuth;
- Google API client;
- manejo de errores.

### Fase 4 — Discovery

- channel;
- uploads playlist;
- paginación;
- sincronización con SQLite.

### Fase 5 — Metadata

- `videos.update`;
- planificación;
- ejecución;
- persistencia de resultados.

### Fase 6 — Quota-aware execution

- costes;
- cuota disponible;
- parada segura;
- reanudación.

### Fase 7 — Thumbnails

- validación;
- upload;
- estado.

### Fase 8 — Playlists

- discovery;
- comprobación de pertenencia;
- insert;
- estado.

### Fase 9 — Publication

- programación;
- validación;
- ejecución.

### Fase 10 — Reporting

- estado del job;
- pendientes;
- errores;
- cuota;
- resumen.

No implementar todas las funcionalidades simultáneamente.

---

# 25. Regla final

La aplicación debe poder detenerse en cualquier momento y responder con
precisión:

```text
¿Qué vídeos conozco?
¿Qué operaciones necesito hacer?
¿Qué operaciones ya hice?
¿Qué operaciones fallaron?
¿Qué operaciones no puedo hacer mediante esta API?
¿Cuánta cuota he consumido?
¿Qué puedo ejecutar ahora?
¿Qué queda para la siguiente ejecución?
```

Si no podemos responder esas preguntas desde el estado persistido, el diseño
todavía no está preparado para producción.
