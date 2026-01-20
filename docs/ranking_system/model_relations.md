# Ranking System

## Modelo de Datos

### Entidades de jugadores y contexto

- Un Player pertenece a un único Country.
- Un Country puede tener cero o muchos Players.
- Un Player puede tener cero o muchos PlayerAlias.
- Un PlayerAlias pertenece a un único Player.
- Un Player puede tener cero o muchas PlayerSocial.
- Cada PlayerSocial pertenece a un único Player.

### Plataforma, región y juego

- Un Event se juega en una única Platform.
- Una Platform puede tener cero o muchos Events.
- Un Event se juega en una única GameVersion.
- Una GameVersion puede tener cero o muchos Events.
- Un Game tiene una o más GameVersions.
- Una GameVersion pertenece a un único Game.
- Un Event puede estar asociado a una única Region.
- Una Region puede tener cero o muchos Events.

### Personajes

- Una CharacterIdentity representa una identidad conceptual de personaje.
- Una CharacterIdentity puede existir en múltiples juegos y versiones.
- Un GameCharacter refiere a una única CharacterIdentity.
- Un GameCharacter pertenece a una única GameVersion.
- Una GameVersion puede tener cero o muchos GameCharacters.
- Un GameCharacter puede ser utilizado en muchas Battles.

### Temporadas y eventos

- Una Season puede contener cero o muchos Events.
- Un Event puede pertenecer opcionalmente a una Season.
- Un Event tiene una única EventType.
- Un EventType puede estar asociado a cero o muchos Events.
- Un Event puede tener enlaces externos (bracket, playlist), ambos opcionales.
- Un Event puede tener una fecha (event_date).

### Duelos

- Un Event contiene uno o más Duels.
- Un Duel pertenece a un único Event.
- Un Duel tiene un único DuelType.
- Un DuelType puede estar asociado a cero o muchos Duels.
- Un Duel puede tener un enlace a video (video_url), opcional.
- Un Duel tiene un orden secuencial dentro de su Event.

### Participantes y equipos en duelos

- Un Duel tiene dos o más DuelParticipants.
- Un DuelParticipant pertenece a un único Duel.
- Un DuelParticipant representa a un único Player.
- Un Player puede participar en muchos Duels.
- Un Duel puede tener cero o muchos DuelTeams.
- Un DuelTeam pertenece a un único Duel.
- Un DuelTeam representa un equipo dentro de un duelo.
- Un DuelTeam puede tener uno o más DuelTeamMembers.
- Un DuelTeamMember pertenece a un único DuelTeam.
- Un DuelTeamMember representa a un único Player.
- Un Team representa una entidad competitiva persistente.
- Un Team puede tener uno o más Players.
- Un Player puede pertenecer a cero o muchos Teams.
- Un DuelTeam puede referenciar opcionalmente a un Team persistente.

### Batallas

- Un Duel se compone de una o más Battles.
- Una Battle pertenece a un único Duel.
- Una Battle tiene un orden secuencial dentro de su Duel.
- Una Battle enfrenta exactamente a dos BattleParticipants.
- Un BattleParticipant pertenece a una única Battle.
- Un BattleParticipant representa a un único Player.
- Un Player puede participar en muchas Battles.
- Un BattleParticipant utiliza un único GameCharacter.

### Rounds

- Una Battle se compone de uno o más Rounds.
- Un Round pertenece a una única Battle.
- Un Round tiene un orden secuencial dentro de la Battle.
- Un Round produce exactamente dos RoundResults.
- Cada RoundResult pertenece a un único Round.
- Un RoundResult corresponde a un único Player.
- Un Player puede tener muchos RoundResults.
- Un RoundResult contiene un result_code que representa el resultado crudo del round.

### Carácterísticas

- Preservación completa de la secuencialidad temporal (eventos, duelos, batallas, rounds).
- Soporte para duelos multi-jugador, duelos por equipos y formatos especiales.
- Capacidad de rankear múltiples entidades (players, teams, characters) según su semántica.
- Flexibilidad total para queries históricas, regionales, por temporada, por plataforma o por formato.
- Separación estricta entre datos crudos y datos calculados, permitiendo recalcular rankings bajo nuevas reglas sin migraciones.
