# Especificación del Sistema de Ranking

## Proyecto: youtube_utilities

## App: ranking_system

## Versión: 1.4

---

## 1. Objetivo

Este documento define formalmente el **contrato conceptual** del sistema de ranking utilizado para evaluar el desempeño competitivo de las entidades del proyecto **youtube_utilities**.

El sistema está diseñado para:

- Reflejar rendimiento competitivo real basado en resultados objetivos.
- Ser invariante ante cambios en la escala de daño.
- Penalizar muestras pequeñas y la inconsistencia histórica.
- Separar explícitamente los niveles semánticos de competencia.
- Evitar inversiones de mérito (el derrotado nunca supera al vencedor).

Este documento es **normativo**: el código debe ajustarse a lo aquí definido.

---

## 2. Entidades competitivas

### 2.1 Tipos de entidades

Existen cuatro tipos de entidades:

- **Players**
- **Teams**
- **Characters**
- **PlayerCharacters**

### 2.2 Nivel semántico de competencia

Las entidades se dividen en **dos niveles competitivos** claramente diferenciados:

#### Duel-level entities

- Players
- Teams

#### Battle-level entities

- Characters
- PlayerCharacters

Este nivel **define completamente** la semántica de las estadísticas y la granularidad de cálculo.

---

## 3. Jerarquía competitiva

### 3.1 Duel-level

```
Round → Battle → Duel → Ranking
```

Aplica a **Players** y **Teams**.

### 3.2 Battle-level

```
Round → Battle → Ranking
```

Aplica a **Characters** y **PlayerCharacters**.

---

## 4. Definición de duelos y batallas

### 4.1 Batallas (Battles)

- Una batalla siempre tiene exactamente dos participantes.
- Los participantes pueden ser Characters o PlayerCharacters.
- En una batalla existen tres resultados posibles: win, loss o draw.
- Las batallas están compuestas por rounds.

### 4.2 Duelos (Duels)

- Un duelo está compuesto por una o más batallas.
- Los duelos solo existen para Players y Teams.
- Un duelo siempre tiene un ganador (no existen empates de duelo).
- En un mismo duelo:
  - Las posiciones de los jugadores pueden variar entre batallas.
  - Las batallas empatadas no determinan la victoria, pero sí aportan puntos.

---

## 5. Sistema atómico de puntos (raw_points)

### 5.1 Definición

Los **raw_points** representan el daño real infligido durante un round.

- El valor máximo por round es la vida total del rival.
- El perdedor puede obtener puntos parciales según el daño infligido.

### 5.2 Invariancia de escala

El sistema es invariante ante cambios de escala de daño:

- Los raw_points escalan linealmente.
- Los factores multiplicativos son adimensionales.
- El orden relativo del ranking no se altera.

---

## 6. Beating Factor

El **beating_factor** mide la proporción de éxito en un conjunto de eventos.

```
beating_factor = (wins + draws × draws_weight + ε) / (total + ε)
```

Parámetros:

- ε = 0.5
- draws_weight = 0.5

Propiedades:

- Nunca es cero.
- Diferencia correctamente 0/x de 1/x.
- Es válido para cualquier nivel:
  - rounds_beating_factor (battle-level)
  - battles_beating_factor (duel-level)

---

## 7. Win Rate Bayesiano

Para evitar sesgos por muestras pequeñas se utiliza un win rate suavizado:

```
adjusted_win_rate = (wins + draws × draw_weight + α) / (games + α + β)
```

Parámetros:

- α = 1
- β = 1
- draw_weight = 0.5

Este valor se utiliza **exclusivamente** para el cálculo del level factor.

---

## 8. Level Factor (lvl_factor)

El **lvl_factor** ajusta los puntos obtenidos según la diferencia de nivel entre competidores.

```
lvl_factor = clamp(
    1 + k × (win_rate_opponent − win_rate_self),
    min_factor,
    max_factor
)
```

### Parámetros

**Battle-level**

```
k = 0.03
min = 0.85
max = 1.15
```

**Duel-level**

```
k = 0.02
min = 0.90
max = 1.10
```

### Invariante fundamental

El lvl_factor **nunca** permite que el derrotado obtenga más puntos que el vencedor.

---

## 9. Cálculo de puntos

### 9.1 Battle-level (Characters, PlayerCharacters)

```
battle_points = raw_points × rounds_beating_factor × battles_lvl_factor
battle_raw_score = Σ battle_points
```

El cálculo se realiza **battle a battle**.

---

### 9.2 Duel-level (Players, Teams)

```
battles_points = Σ battle_points
duel_points = battles_points × battles_beating_factor × duels_lvl_factor
duel_raw_score = Σ duel_points
```

El cálculo se realiza **duel a duel**.

---

## 10. Semántica de estadísticas

### 10.1 Duel-level entities

- events_played = duelos jugados
- wins = duelos ganados
- losses = duelos perdidos
- draws = 0 (no existen empates de duelo)
- win_rate = duel win rate

### 10.2 Battle-level entities

- events_played = batallas jugadas
- wins = batallas ganadas
- losses = batallas perdidas
- draws = batallas empatadas
- win_rate = battle win rate

---

## 11. Consistency Factor

```
consistency_factor = games_played / (games_played + C)
```

Parámetro:

- C = 10

Penaliza muestras pequeñas e inconsistencia histórica.

---

## 12. Score

### Duel-level

```
score = duel_raw_score × consistency_factor
```

Se actualiza duelo a duelo.

### Battle-level

```
score = battle_raw_score × consistency_factor
```

Se actualiza batalla a batalla.

---

## 13. Rating

### Valor inicial

```
rating_initial = 1500
```

### Actualización

**Duel-level**

`rating_new = rating_old + duel_points × k_rating`

**Battle-level**

`rating_new = rating_old + battle_points × k_rating`

Parámetro:

- k_rating = 0.02

---

## 14. Invariantes globales

1. El vencedor nunca obtiene menos puntos que el derrotado.
2. Ningún factor invierte resultados competitivos.
3. El sistema es invariante a la escala de daño.
4. Las muestras pequeñas están penalizadas.
5. FT variables no rompen el modelo.
6. El nivel semántico de la entidad define el cálculo.

---

## 15. Estado del documento

Este documento define la **base contractual** del sistema de ranking.  
Cualquier cambio requiere una nueva versión.
