# Guía para Desarrolladores — youtube_utilities

## 1. Cómo Pensar el Proyecto

Antes de escribir código:

- Identifica si es dominio, servicio u orquestador
- Pregunta: ¿coordina o ejecuta?
- Pregunta: ¿conoce contexto global?

---

## 2. Agregar una Nueva App

1. Crear carpeta en apps/
2. Definir Processor
3. Usar servicios existentes
4. No duplicar lógica
5. Documentar README.md

---

## 3. Agregar un Servicio

- Una responsabilidad
- Sin paralelización
- Sin estado global
- Entradas y salidas explícitas

---

## 4. Sistema de Ranking

Pasos:

1. DataProvider obtiene eventos
2. Calculators procesan battles/duels
3. RankingEngine acumula score
4. Rating se deriva del score

Soporta:

- Ranking global
- Single Player Performance Mode
- Torneos
- Temporadas
- Países
- Plataformas

---

## 5. Buenas Prácticas

- Validar temprano
- Prefijos explícitos
- Docstrings como contratos
- No asumir defaults mágicos
- Tests sobre dominio antes que servicios

---

## 6. Extensiones Futuras

- Dashboards de ranking
- Exportadores CSV / JSON
- API REST
- Machine Learning (predicción, detección de anomalías)
- Visualización temporal de performance
