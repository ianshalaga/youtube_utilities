# Base de datos

## Validaciones de loader

### 1

- Winner no está restringido a participantes en:
  - Battle (winner_id / loser_id)
  - Round (winner_id / loser_id)
  - Duel (winner_id / winner_team_id)

No hay constraint que garantice que el winner pertenece al conjunto de participantes. Eso debe vivir en el loader. No es error del modelo, pero es punto crítico operativo.

### 2

- Duel permite 0 participants. Nada impide:
  - Crear Duel sin DuelParticipant
  - Crear Duel de equipo sin DuelTeam

Eso es correcto a nivel relacional, pero debe validarse en loader.

### 3

- BattleParticipant.duel_team_id no está protegido. En eventos de equipos:
  - battle_participant.duel_team_id debería ser NOT NULL.
  - En eventos individuales debería ser NULL.

Eso no está restringido. Lógica en loader:

```Python
if duel has duel_teams:
    duel_team_id required
else:
    duel_team_id must be NULL
```

### 4

- Agregar constraint lógico en Duel. Actualmente:

(winner_id IS NOT NULL AND winner_team_id IS NULL)
OR
(winner_id IS NULL AND winner_team_id IS NOT NULL)

Eso obliga siempre a tener uno de los dos. Correcto según ranking_system. Pero hay un detalle conceptual:

En duelo individual:

- winner_team_id NULL
- winner_id NOT NULL

En duelo por equipos:

- winner_team_id NOT NULL
- winner_id NULL

Eso está bien. Pero no se valida coherencia con la existencia de duel_teams. No puede hacerse con CheckConstraint estándar. Debe validarse en loader.

### 5

- BattleParticipant no valida cardinalidad real. Modelo permite:
  - 3 participantes en una battle.
  - 4 participantes en una battle.

El dominio asume 2. Eso no es error estructural, pero es una debilidad semántica. Validarlo estrictamente en loader o agregar validación a nivel aplicación.

### 6

- BattleParticipant.duel_team_id es débil semánticamente. Permite:
  - duel_team_id NULL.
  - duel_team_id que no pertenezca al mismo duel que la battle.

- No puede resolverse con FK simple. Pero se debe validar estrictamente en loader:
  - Que si battle pertenece a duelo por equipos, entonces duel_team_id no sea NULL.
  - Que duel_team.duel_id == battle.duel_id.

Es un punto frágil del modelo.

### 7

BattleParticipant permite cardinalidad > 2

Modelo permite 3 o más participantes en battle.

Si dominio exige 2 siempre, debes:

Validarlo en loader

O agregar check application-level

No se puede resolver en DB sin trucos complejos.

### 8

Duel no valida coherencia entre winner y tipo de duelo

Nada impide:

Duel con winner_id

Y también tener duel_teams cargados

Es correcto relacionalmente,
pero frágil semánticamente.

Debe validarse en loader.
