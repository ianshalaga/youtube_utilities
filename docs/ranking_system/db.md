# Base de Datos

## Validaciones obligatorias en Loader / Aplicación

El modelo relacional es estructuralmente correcto, pero existen
debilidades semánticas que deben validarse fuera de la base de datos.

Las siguientes reglas deben implementarse explícitamente en el loader o
en la capa de aplicación.

---

## 1. Coherencia de Winner con Participantes

### Problema

No existe un constraint que garantice que el ganador pertenece al
conjunto de participantes en:

- `Battle (winner_id / loser_id)`
- `Round (winner_id / loser_id)`
- `Duel (winner_id / winner_team_id)`

La base de datos permite asignar como ganador una entidad que no
participa en ese contexto competitivo.

### Validación requerida

- En `Battle`:
  - `winner_id` y `loser_id` deben existir en `BattleParticipant` de
    esa battle.
- En `Round`:
  - `winner_id` y `loser_id` deben existir en `RoundResult` de ese
    round.
- En `Duel` individual:
  - `winner_id` debe existir en `DuelParticipant`.
- En `Duel` de equipo:
  - `winner_team_id` debe existir en `DuelTeam`.

---

## 2. Cardinalidad mínima de Participantes

### 2.1 Duel sin participantes

El modelo permite:

- Crear un `Duel` sin `DuelParticipant`.
- Crear un `Duel` de equipo sin `DuelTeam`.

#### Validación requerida

- Duel individual → mínimo 2 `DuelParticipant`.
- Duel de equipo → exactamente 2 `DuelTeam`.

---

### 2.2 Battle con más de 2 participantes

El modelo permite 3 o más `BattleParticipant` en una battle.

El dominio asume enfrentamientos 1v1.

#### Validación requerida

- Cada `Battle` debe tener exactamente 2 `BattleParticipant`.

---

## 3. Coherencia en Eventos por Equipos

### 3.1 duel_team_id en BattleParticipant

Actualmente se permite:

- `duel_team_id = NULL`
- `duel_team_id` que no pertenezca al mismo `Duel` que la `Battle`

#### Validaciones requeridas

Si el duelo es por equipos:

- `battle_participant.duel_team_id` debe ser NOT NULL.
- `duel_team.duel_id` debe coincidir con `battle.duel_id`.

Si el duelo es individual:

- `battle_participant.duel_team_id` debe ser NULL.

---

## 4. Coherencia entre tipo de Duel y Winner

Actualmente existe el siguiente constraint:

```sql
(winner_id IS NOT NULL AND winner_team_id IS NULL)
OR
(winner_id IS NULL AND winner_team_id IS NOT NULL)
```

Este constraint garantiza que exista un único tipo de ganador.

### Problema

No se valida coherencia entre:

- El tipo real del duelo (individual vs equipos)
- La existencia de `DuelTeam`
- El tipo de winner asignado

### Validación requerida

- Si existen `DuelTeam` asociados:
  - `winner_team_id` debe estar definido.
  - `winner_id` debe ser NULL.
- Si no existen `DuelTeam`:
  - `winner_id` debe estar definido.
  - `winner_team_id` debe ser NULL.

---

## 5. Resumen de Reglas Críticas

El loader debe garantizar:

1. El winner siempre pertenece al conjunto correcto.
2. El Duel tiene cardinalidad válida de participantes.
3. La Battle tiene exactamente 2 participantes.
4. `duel_team_id` es coherente con el tipo de duelo.
5. El tipo de winner coincide con el tipo de duelo.

---

## 6. Principio General

El modelo relacional garantiza la estructura.

La coherencia competitiva debe garantizarse en el loader o en la capa de
aplicación.

No es posible imponer estas reglas mediante constraints SQL estándar sin
introducir complejidad excesiva.

## 7. EventType vs event_type columna v2

Loader v2:

event_type explícito

loaders

Modelo:

Tiene EventType FK

Correcto, pero no hay constraint que alinee:

event_type = team_tournament

con existencia de DuelTeam

Eso es validación aplicación.

Pero estructuralmente falta coherencia cruzada.

Recomendación:

Validar en loader que:

event.event_type == team_tournament
↔ existen duels con is_team_duel = TRUE

## 8. Falta alineación estructural EventType ↔ is_team_duel

Loader v2:

event_type explícito

loaders

Modelo:

EventType FK

Duel.is_team_duel independiente

Nada impide:

EventType = tournament

Duel.is_team_duel = TRUE

Eso rompe coherencia estructural.

No es resoluble con FK simple, pero deberías:

Validarlo en loader

O considerar constraint a nivel aplicación que:

event.event_type.name == "team_tournament"
↔
duel.is_team_duel = TRUE
