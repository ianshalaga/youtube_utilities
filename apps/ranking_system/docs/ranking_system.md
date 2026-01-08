# Especificación del Sistema de Ranking

## Proyecto: youtube_utilities

## Módulo: ranking_system

## Versión: 1.2

---

## 1. Objetivo

Este documento define formalmente el sistema de ranking utilizado para
evaluar el desempeño competitivo de las entidades del proyecto
**youtube_utilities**.

El sistema está diseñado para:

- Reflejar rendimiento real basado en resultados objetivos
- Ser invariante ante cambios de escala de daño
- Penalizar muestras pequeñas e inconsistencia histórica
- Separar correctamente niveles semánticos de competencia
- Evitar inversiones de mérito (el derrotado nunca supera al vencedor)

---

## 2. Alcance por tipo de entidad

### 2.1 Player

Los **players** son la única entidad que participa en **duelos**.
Por lo tanto, el sistema completo de ranking aplica únicamente a ellos.

Jerarquía competitiva:

`Round → Battle → Duel → Player Ranking`

Los players acumulan:

- `battle_points`
- `duel_points`
- `score`
- `rating`

---

### 2.2 PlayerCharacter y Character

Las entidades **player_character** y **character**:

- No participan en duelos
- Pueden cambiar dentro de un mismo duelo
- Su máxima unidad competitiva es la **battle**

Jerarquía aplicable:

`Round → Battle → Character Ranking`

Consecuencias:

- No existe capa `duel`
- No existen `duel_points`
- No existe `rating`
- El ranking final se basa exclusivamente en `battle_points`

---

## 3. Sistema atómico de puntos (raw_points)

### 3.1 Definición

Los `raw_points` representan el **daño real infligido** durante un round.

- El valor máximo por round es la vida total del rival (`H`)
- El perdedor de un round puede obtener puntos parciales

Ejemplo:

- Round ganado: `H`
- Round perdido infligiendo `H − 1`: `H − 1`

Este sistema es lineal respecto a `H`.

---

### 3.2 Invariancia a la escala de daño

Si el valor máximo de daño cambia (por ejemplo, de `240` a `1000`):

- Todos los `raw_points` escalan linealmente
- Los factores multiplicativos permanecen adimensionales
- El orden relativo del ranking no se altera

El sistema es **invariante ante cambios de escala de daño**.

---

## 4. Beating factor

El `beating_factor` mide la proporción de éxito de una entidad.

Definición:

`beating_factor = (wins + ε) / (total + ε)`

Parámetro:

- `ε = 0.5`

Propiedades:

- Nunca es cero
- Diferencia correctamente 0/x de 1/x
- Escala automáticamente con FT variables
- Es válido para cualquier nivel semántico

---

## 5. Win rate bayesiano

Para evitar sesgos por muestras pequeñas se utiliza un win rate suavizado:

`adjusted_win_rate = (wins + α) / (games + 2α)`

Parámetro:

- `α = 1`

Este valor se utiliza **exclusivamente** para el cálculo de los
`lvl_factor`.

---

## 6. Level factor (lvl_factor)

El `lvl_factor` ajusta los puntos obtenidos en función de la diferencia
de nivel entre los competidores.

Definición general:

```Python
lvl_factor = clamp(
    1 + k × (win_rate_opponent − win_rate_self),
    min_factor,
    max_factor
)
```

---

### 6.1 Battles lvl_factor

Parámetros:

- `k = 0.03`
- `min_factor = 0.85`
- `max_factor = 1.15`

---

### 6.2 Duels lvl_factor (solo players)

Parámetros:

- `k = 0.02`
- `min_factor = 0.90`
- `max_factor = 1.10`

---

### 6.3 Invariante fundamental

Bajo ningún escenario el `lvl_factor` permite que el derrotado obtenga
más puntos que el vencedor, incluso con:

- Daño parcial refinado
- FT elevados
- Escalas de daño variables

---

## 7. Cálculo de battle_points

Los `battle_points` se calculan para todas las entidades competitivas.

`battle_points = raw_points * rounds_beating_factor * battles_lvl_factor`

---

## 8. Cálculo de duel_points (solo players)

Primero se agregan los puntos de las battles:

`battles_points = Σ battle_points`

Luego se calcula:

`duel_points = battles_points * battles_beating_factor * duels_lvl_factor`

Los `duel_points` son:

- Atómicos
- Inmutables
- Exclusivos de players

---

## 9. Consistency factor

El `consistency_factor` penaliza la inconsistencia histórica y las
muestras pequeñas.

Definición:

`consistency_factor = games_played / (games_played + C)`

Parámetro:

- `C = 10`

---

## 10. Score (ranking histórico)

### 10.1 Players

`raw_score = Σ duel_points`
`score = raw_score * consistency_factor`

### 10.2 Characters y PlayerCharacters

`raw_score = Σ battle_points`
`score = raw_score * consistency_factor`

El `score`:

- Es permanente
- No se reinicia
- Representa el legado competitivo

---

## 11. Rating (ranking competitivo actual)

### 11.1 Alcance

El `rating` existe únicamente para players.

---

### 11.2 Valor inicial

`rating_initial = 1500`

Este valor representa un punto neutro y facilita comparación histórica.

---

### 11.3 Actualización del rating

`rating_new = rating_old + duel_points × k_rating`

Parámetro definido:

`k_rating = 0.02`

---

### 11.4 Temporalidad

- El rating es estacional
- Puede reiniciarse por temporada
- El score no se reinicia

---

## 12. Relación Score vs Rating

| Métrica | Significado              | Persistencia |
| ------- | ------------------------ | ------------ |
| Score   | Trayectoria histórica    | Permanente   |
| Rating  | Forma competitiva actual | Estacional   |

Ambas métricas coexisten y cumplen funciones distintas.

---

## 13. Invariantes globales

1. El vencedor nunca obtiene menos puntos que el derrotado
2. Ningún factor invierte resultados competitivos
3. El sistema es invariante a la escala de daño
4. Las muestras pequeñas están penalizadas
5. FT variables no rompen el modelo
6. Todos los parámetros son explícitos y versionables

---

## 14. Estado del documento

Este documento define la **base contractual** del sistema de ranking.
Cualquier cambio posterior debe implicar una nueva versión.
