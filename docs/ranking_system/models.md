🔷 Núcleo Competitivo
Season

Representa un período competitivo delimitado en el tiempo.
Agrupa múltiples eventos bajo una misma etapa histórica del ranking.

Event

Representa un torneo o competencia específica dentro de una season.
Contiene múltiples duelos y define contexto regional, tipo de evento y versión del juego.

Duel

Unidad competitiva dentro de un evento.
Puede tener dos o más participantes.
Tiene un único ganador explícito y agrupa varias battles.

DuelParticipant

Asocia jugadores a un duelo.
Define el conjunto de competidores de ese enfrentamiento.

DuelTeam

Representa un equipo participante dentro de un duelo por equipos.

DuelTeamMember

Asocia jugadores a un equipo específico dentro de un duelo.

Battle

Subunidad de un duelo.
Generalmente representa un enfrentamiento directo (ej. 1v1).
Tiene ganador/loser explícitos o puede terminar en empate.

BattleParticipant

Asocia jugadores (y su personaje elegido) a una battle.
Define la composición concreta del enfrentamiento.

Round

Unidad mínima competitiva dentro de una battle.
Tiene resultado estructural explícito (winner/loser/draw).

RoundResult

Resultado individual de un jugador en un round.
Contiene el result_code, que describe cómo terminó el round desde su perspectiva (W, LB, LY, PW, PL, D).
Es la base para el cálculo de puntos.

🔷 Dominio del Juego
Franchise

Marca o universo al que pertenece un juego (ej. una saga).

Game

Juego específico dentro de una franquicia.

Platform

Plataforma donde se ejecuta el juego (PS, PC, etc.).

GameVersionPlatform

Combinación específica de juego + plataforma + versión.
Define el entorno técnico exacto del evento.

CharacterIdentity

Identidad conceptual de un personaje dentro de una franquicia.

GameCharacter

Instancia jugable de un personaje en una versión/plataforma concreta.

Stage

Escenario donde se desarrolla una battle.
Depende de la versión del juego.

🔷 Participantes
Player

Competidor individual del sistema.

PlayerAlias

Alias alternativo usado por un jugador.

PlayerSocialAccount

Cuenta social asociada a un jugador en una plataforma específica.

Team

Entidad colectiva reutilizable en distintos duelos por equipos.

Country

País asociado a un jugador.

Region

Región competitiva donde se desarrolla un evento.

🔷 Clasificación y Tipos
EventType

Clasificación del evento (ej. major, regional, online).

DuelType

Tipo de duelo (individual, por equipos, etc.).

SocialPlatform

Plataforma social (Twitter, Twitch, etc.).
