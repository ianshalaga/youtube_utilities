# Arquitectura y Buenas Prácticas Aplicadas

## Proyecto: youtube_utilities

Este documento resume y organiza los principios de diseño, arquitectura
y buenas prácticas aplicadas durante el desarrollo del proyecto
**youtube_utilities**.

El objetivo no es documentar funcionalidades concretas, sino **explicitar
el conocimiento técnico y las decisiones de ingeniería** que guían el sistema.

---

## 1. Filosofía general del proyecto

Este proyecto se rige por los siguientes principios:

- Separación estricta de responsabilidades
- Preferencia por composición sobre herencia
- Orquestadores sin lógica técnica
- Servicios pequeños, explícitos y testeables
- Infraestructura desacoplada del dominio
- Evitar estados implícitos y efectos secundarios ocultos

El sistema se diseña para **ser entendido, extendido y mantenido**, no solo
para “funcionar”.

---

## 2. Orquestadores vs Servicios

### 2.1 Orquestadores (Processors / Apps)

Un **orquestador**:

- Coordina servicios
- Define el flujo de ejecución
- Decide _cuándo_ ocurre algo
- NO implementa lógica técnica compleja
- NO ejecuta herramientas externas directamente

Ejemplos:

- `VideoJoinerProcessor`
- `VideoMusicProcessor`
- Futuro: `VideoConverterProcessor`

Características clave:

- Son el único punto que conoce el “caso de uso”
- Son ideales para paralelización
- Son el lugar correcto para manejar errores globales

> Regla de oro:  
> **Si una clase sabe ejecutar ffmpeg, no debería saber cuándo hacerlo.**

---

### 2.2 Servicios

Un **servicio**:

- Hace UNA cosa bien
- No coordina otros servicios
- No conoce el contexto global
- Puede ser reutilizado en múltiples apps

Ejemplos:

- `MKVMergeRunner`
- `VideoPartitioner`
- `TimestampFileBuilder`
- `EndScreenGenerator`
- `AudioConverter`
- `VideoConverter`

Características:

- Interfaces claras
- Entrada → salida explícita
- Fácil de testear
- Sin efectos colaterales ocultos

---

## 3. Infraestructura vs Dominio

### 3.1 Infraestructura

Infraestructura es todo lo que:

- Ejecuta herramientas externas
- Interactúa con el sistema operativo
- Depende de paths, subprocess, ffmpeg, mkvmerge, etc.

Ejemplos:

- `FFProbeMediaProbeProvider`
- `MKVMergeRunner`
- `AudioConverter`
- `VideoConverter`

Reglas:

- No contiene lógica de negocio
- No toma decisiones semánticas
- Puede fallar y lanzar excepciones técnicas

---

### 3.2 Dominio

El dominio:

- Modela conceptos
- Define invariantes
- Representa conocimiento del problema

Ejemplos:

- `VideoSignature`
- Futuro: `VideoEncoding`
- Criterios de compatibilidad
- Reglas de particionado

Regla:

> El dominio **no sabe** cómo se ejecuta ffmpeg  
> La infraestructura **no sabe** qué es “compatible”

---

## 4. Validación temprana y preventiva

Un patrón recurrente del proyecto es:

> **Fall early, fail loud**

Ejemplos:

- Validar compatibilidad de videos ANTES de unir
- Validar parámetros antes de ejecutar procesos pesados
- Validar existencia de archivos y directorios

Esto reduce:

- Ejecuciones largas fallidas
- Resultados corruptos
- Bugs difíciles de depurar

---

## 5. Particionado de videos: enfoque correcto

### 5.1 Problema real

- No se pueden cortar videos arbitrariamente
- No se pueden reordenar
- Se desea equilibrio temporal entre partes

### 5.2 Enfoque aplicado

1. Calcular duración total
2. Determinar número de partes (K)
3. Calcular duración ideal por parte
4. Agrupar videos contiguos minimizando la desviación

Esto evita:

- Últimas partes ridículamente cortas
- Acumulación desbalanceada
- Heurísticas locales incorrectas

---

## 6. Concatenación segura de video

### 6.1 mkvmerge y el operador `+`

La concatenación correcta en mkvmerge se hace con:

video1 + video2 + video3

No con:

video1 video2 video3

El operador `+` indica concatenación temporal real.

---

### 6.2 Compatibilidad binaria

Para que mkvmerge funcione sin corrupción:

- Codec idéntico
- Resolución idéntica
- Framerate idéntico
- Streams de audio compatibles
- Mismo timebase

Cualquier desviación puede producir:

- Videos que “crashean” a mitad
- Reproductores inestables
- Archivos gigantes pero inválidos

---

## 7. End screens: decisión arquitectónica clave

### 7.1 Problema detectado

- Usar videos externos como end screens genera incompatibilidades
- Convertir “para que coincidan” es frágil y complejo

### 7.2 Solución correcta

Generar la end screen a partir del **mismo video**:

- Tomar un fragmento (ej. 20s)
- Reemplazar audio
- Aplicar filtros visuales

Ventajas:

- Compatibilidad garantizada
- mkvmerge no distingue el cambio
- Pipeline estable y simple

Este enfoque elimina una clase completa de errores.

---

## 8. Conversión multimedia: cuándo y cómo

### 8.1 Audio

- Conversión controlada
- Normalización EBU R128
- Uso explícito de ffmpeg
- Archivos temporales claramente marcados

### 8.2 Video

- Conversión solo cuando es necesario
- Formato explícito O derivado de referencia
- No copiar streams ciegamente
- No asumir valores mágicos

Principio clave:

> Convertir **es una operación pesada y delicada**  
> Concatenar **es una operación frágil**

---

## 9. Paralelización segura

### 9.1 Qué se paraleliza

- **Partes finales independientes**
- Nunca pasos que compartan archivos temporales
- Nunca escritura concurrente en el mismo path

### 9.2 Dónde se paraleliza

- En el orquestador
- Nunca dentro de servicios
- Nunca dentro de runners

### 9.3 Regla fundamental

> Si una función puede ejecutarse en paralelo,  
> debe ser **completamente autocontenida**.

---

## 10. Gestión de temporales

Buenas prácticas aplicadas:

- Directorios temporales explícitos
- Vida útil clara
- Limpieza garantizada (`finally`)
- Nunca confiar en nombres generados por herramientas externas

Los temporales:

- Son infraestructura
- No deben “filtrarse” al dominio
- No deben sobrevivir al proceso

---

## 11. Naming y claridad semántica

El proyecto prioriza:

- Nombres largos pero claros
- Métodos que hacen exactamente lo que dicen
- Prefijos `_` solo para encapsulación real
- Documentación como contrato, no como comentario redundante

Ejemplo correcto:

\_process_single_part

Ejemplo incorrecto:

doStuff

---

## 12. Conclusión

Este proyecto aplica principios que se encuentran en:

- Arquitectura hexagonal
- Clean Architecture
- Diseño orientado a dominio (ligero)
- Ingeniería de pipelines multimedia reales

No es un proyecto “académico” ni un script utilitario:
es un **sistema diseñado para crecer sin romperse**.

El mayor logro no es que funcione,
sino que **puede seguir evolucionando sin reescribirse**.
