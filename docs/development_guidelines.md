# Guía de desarrollo

Esta guía resume convenciones técnicas observadas en el código y pautas para extenderlo. El protocolo de trabajo para agentes está en `AGENTS.md`; la arquitectura y el mapa de carpetas se describen en `architecture.md` y `project_structure.md`.

## Antes de implementar

1. Localizar la interfaz que inicia el flujo y seguir las llamadas hasta la aplicación, servicios y dominio implicados.
2. Revisar componentes y pruebas existentes antes de añadir una nueva clase, módulo o dependencia.
3. Identificar quién coordina el caso de uso, quién ejecuta la capacidad técnica y dónde vive la regla de negocio.
4. Comprobar si hay efectos externos, persistencia o estado compartido y mantenerlos visibles en las dependencias.

## Responsabilidades

- **Dominio (`domain/`)**: representar conceptos, reglas y validaciones del problema, sin depender de frameworks o servicios externos.
- **Aplicaciones (`applications/`)**: coordinar los pasos de un caso de uso; varios flujos usan una clase `Processor` como punto principal.
- **Servicios (`services/`)**: implementar capacidades técnicas e integraciones, como acceso a APIs, persistencia, procesos externos y operaciones multimedia.
- **Composición (`composition/`)**: construir e inyectar dependencias compartidas cuando el proyecto tenga un factory para ese flujo.
- **Interfaces (`interfaces/`)**: traducir argumentos o solicitudes a llamadas de aplicación y presentar los resultados.
- **Core (`core/`)**: alojar capacidades transversales; evitar trasladar aquí lógica específica de una aplicación.

Estas responsabilidades describen la dirección deseada. Algunas aplicaciones auxiliares tienen estructuras propias; seguir el patrón local si el área no usa estas capas de forma completa.

## Añadir o modificar un flujo

1. Mantener los cambios acotados a los módulos necesarios.
2. Preferir las estructuras existentes bajo `applications/`, `domain/`, `services/`, `composition/` e `interfaces/` en lugar de crear directorios paralelos.
3. Inyectar dependencias por constructor o por la composición existente; evitar estado global implícito.
4. Mantener los detalles de SDKs, bases de datos, sistema de archivos y procesos externos en el límite que ya los gestiona.
5. Actualizar la interfaz correspondiente solo si el flujo debe exponerse desde CLI o web. La existencia de una carpeta de aplicación no la registra automáticamente.
6. Actualizar la documentación arquitectónica o de estructura si cambia una frontera, un punto de entrada o una convención compartida.

## Convenciones Python

- Usar `snake_case` para módulos, funciones y variables; `PascalCase` para clases.
- Preferir `pathlib.Path` para rutas, como en los procesadores e interfaces existentes.
- Añadir anotaciones de tipos a APIs públicas y conservar las firmas explícitas de los módulos cercanos.
- Usar nombres que indiquen la intención y la unidad o contexto cuando sea relevante; evitar abreviaturas ambiguas.
- Mantener funciones y clases con una responsabilidad identificable.
- Escribir docstrings para explicar contratos, precondiciones, efectos secundarios o decisiones que no sean evidentes. Evitar comentarios que repitan literalmente el código.
- Gestionar errores en la capa que puede decidir si continuar, reintentar, informar o detener el caso de uso; no ocultar excepciones genéricas.

## Integraciones y estado

- Encapsular llamadas a APIs externas en los módulos de servicio correspondientes; no propagar tipos del SDK a dominio o presentación.
- Reutilizar `services/system/process_runner.py` y los runners/proveedores multimedia existentes al invocar herramientas de sistema, cuando corresponda al flujo.
- Mantener separadas las persistencias que pertenecen a dominios o aplicaciones distintos. En particular, YouTube y ranking tienen módulos de almacenamiento separados.
- No asumir que los datos locales (`*.db`, tokens, manifiestos o configuración) pueden regenerarse o sobrescribirse; comprobar primero su uso.
- Para operaciones reanudables, persistir los estados mediante el repositorio del flujo y no introducir otro formato como fuente de verdad sin una decisión explícita.

## Pruebas y validación

Las pruebas usan pytest y están organizadas bajo `tests/` por dominio, servicios, aplicaciones, composición, interfaces e integración. `pytest.ini` define `integration` y `real_youtube` para pruebas que dependen de servicios externos.

- Añadir o ajustar pruebas en la carpeta correspondiente al comportamiento modificado.
- Probar reglas de dominio sin infraestructura cuando sea posible.
- Usar dobles de prueba para aislar APIs, procesos y persistencia en pruebas unitarias.
- Identificar las pruebas de integración que requieren credenciales, red o herramientas instaladas; no ejecutarlas como si fueran locales aisladas.
- Al informar resultados, especificar qué comandos se ejecutaron y qué dependencias o comprobaciones quedaron pendientes.

## Interfaz web

La web vive dentro de `interfaces/web/` y usa Django. Mantener vistas, formularios, URLs, templates y recursos estáticos dentro de la app web correspondiente. Si se cambia un flujo web, revisar también el registro en `config/urls.py` y `config/settings.py` cuando aplique.

El frontend usa fuentes en `static_src/` y artefactos servidos en `static/`; revisar los scripts de `package.json` antes de cambiar o regenerar recursos.

## Dependencias

No añadir paquetes por conveniencia si la biblioteca estándar o una dependencia existente resuelve el problema. Antes de incorporar una dependencia, indicar el uso concreto y actualizar el manifiesto adecuado: `requirements.txt` para Python o `interfaces/web/package.json` para herramientas frontend.

