# Loaders

## Loader Legacy

### Columnas Legacy

- **season**: Nombre de la temporada. Solo hay dos temporadas S1 y S2.
- **event**: Nombre del evento. Hay 4 tipos de nombres de eventos relacionados a 4 tipos de eventos. "SSLT {number}" (Seyfer Studios Lightning Tournament) de tipo "tournament", "SSLTT {number}" (Seyfer Studios Lightning Team Tournament) de tipo "team_tournament", "SSLL {number}" (Seyfer Studios Lightning League) de tipo "league" y "SSLTSE {number}" (Seyfer Studios Lightning Tournament Special Edition) de tipo "special_tournament".
- **duel**: Es un número entero que siempre comienza en 1 para cada evento y se incrementa con cada duelo del mismo. Si un evento tiene 10 duelos, el valor de duel será 1, 2, 3, 4, 5, 6, 7, 8, 9 y 10.
- **combat**: Es un número entero que siempre comienza en 1 para cada duelo y se incrementa con cada batalla del mismo. Si un duelo tiene 10 batallas, el valor de combat será 1, 2, 3, 4, 5, 6, 7, 8, 9 y 10.
- **player1**: Nombre del jugador 1.
- **player2**: Nombre del jugador 2.
- **character1**: Nombre del personaje usado por el jugador 1.
- **character2**: Nombre del personaje usado por el jugador 2.
- **p1_country**: Nombre del países de origen del jugador 1.
- **p2_country**: Nombre del países de origen del jugador 2.
- **stage**: Nombre del escenario en el que se juega la batalla.
- **video**: Enlace al video del duelo en YouTube.
- **date**: Fecha del evento. Formato ISO 8601 (YYYY-MM-DD).
- **playlist**: Enlace a una lista de reproducción de YouTube que contiene todos los duelos del evento.
- **brackets**: Enlace al sitio web donde se organiza el evento.
- **platform**: Plataforma de juego en la que se juega. En este caso solo hay dos, "PC" (Steam) y "PS4" (PlayStation 4).
- **game**: Nombre del juego. En este caso solo hay un juego, "Soulcalibur VI".
- **version**: Versión del juego al que se juega. En este caso solo hay una versión, "2.31".
- **region**: Nombre de la región a la que pertencen los jugadores. En este caso solo hay una región, "SAS" (South America South).
- **r1_p1**: resultado del round 1 para el jugador 1.
- **r2_p1**: resultado del round 2 para el jugador 1.
- **r3_p1**: resultado del round 3 para el jugador 1.
- **r4_p1**: resultado del round 4 para el jugador 1.
- **r5_p1**: resultado del round 5 para el jugador 1.
- **r1_p2**: resultado del round 1 para el jugador 2.
- **r2_p2**: resultado del round 2 para el jugador 2.
- **r3_p2**: resultado del round 3 para el jugador 2.
- **r4_p2**: resultado del round 4 para el jugador 2.
- **r5_p2**: resultado del round 5 para el jugador 2.
- **p1_team**: Nombre del equipo al que representa el jugador 1 en un duelo de equipo.
- **p2_team**: Nombre del equipo al que representa el jugador 2 en un duelo de equipo.
- **team_duel**: Es un número entero que siempre comienza en 1 para cada evento de equipos y se incrementa con cada duelo de equipos del mismo. Si un evento de equipos tiene 10 duelos de equipos, el valor de team_duel sera 1, 2, 3, 4, 5, 6, 7, 8, 9 y 10.
- **duel_type**: Tipo de duelo. Puede ser FT2, FT3, FT5, etc (First to X).

### Filas Legacy

- Cada fila representa una batalla. De este modo un evento con 10 duelos de 5 batallas tendría 50 filas.

### Aclaraciones Legacy

- El tipo del evento se debe determinar a partir del nombre del evento.
- La franquicia a la que pertenece el juego se debe determinar a partir del nombre del juego. Para "Soulcalibur VI" la franquicia es "Soulcalibur".
- Los resultados de los rounds no son valores numéricos si no que son valores codificados.
- Los resultados de los rounds permiten determinar los puntos obtenidos por cada jugador por cada round.
- Los resultados de los rounds pueden ser: "W" (win), "PW" (perfect win), "LB" (loss blue), "LY" (loss yellow), "PL" (perfect loss), "D" (draw) o "0" (zero).
- Los resultados "W" y "PW" indican que el jugador ganó el round.
- Los resultados "LB", "LY" y "PL" indican que el jugador perdió el round.
- El resultado "D" indica que el round fue un empate.
- El resultado "0" indica que no hubo round jugado. Existe debido al número fijo de rounds (columnas) por batalla. Todas las batallas tienen un máximo posible de 5 rounds debido a que las batallas son FT3 de rounds.
- Cuando el resultado de uno de los jugadores es "PW", el resultado del otro jugador es "PL".
- Cuando el resultado de uno de los jugadores es "W", el resultado del otro jugador puede ser "LB" o "LY".
- Cuando el resultado de uno de los jugadores es "D", el resultado del otro jugador es "D".
- Cuando el resultado de uno de los jugadores es "0", el resultado del otro jugador es "0".
- El ganador de un round se debe inferir a partir del resultado del round.
- Los códigos "W", "PW" y "D" indican que el jugador ganó el round.
- Los códigos "LB", "LY", "PL" indican que el jugador perdió el round.
- El ganador de la batalla se debe inferir a partir de los resultados de los rounds.
- El ganador de la batalla es aquel que ha ganado más rounds.
- Si ambos participantes tienen la misma cantidad de rounds ganados, la batalla es un empate.
- Los duelos tiene dos o más participantes.
- Los duelos no se pueden empatar. Siempre hay un ganador.
- El ganador de un duelo se debe inferir a partir de los resultados de las batallas.
- El ganador de un duelo es aquel que ha ganado más batallas.
- Las columnas **team_duel**, **p1_team** y **p2_team** están vacías si el evento no es un evento de equipos. Es decir, si el evento no es de tipo "team_tournament".
- En eventos de equipos la columna **duel_type** hace referencia al duelo de equipo. Es decir, al duelo enumerado según la columna **team_duel**.
- En los eventos de equipos los duelos de equipos están conformados por duelos entre jugadores (columna **duel**) de esos equipos.

## Loader v2

### Columnas v2

- Se conservan las columnas (algunas renombradas): season, event, duel (p_duel, players duel), combat (battle), player1 (p1, player 1), player2 (p2, player 2), character1 (p1_ch, player 1 character), character2 (p2_ch, player 2 character), p1_country, p2_country, stage, video, date, playlist, brackets, platform, game, version, region, p1_team, p2_team, team_duel (t_duel, teams duel), duel_type.
- No es necesaria una columna para la franquicia del juego. El juego se identifica mediante el nombre del juego a través de un mapper.
- **p1_result**: resultado del round para el jugador 1.
- **p2_result**: resultado del round para el jugador 2.
- **r_winner**: jugador / personaje ganador del round.
- **b_winner**: jugador / personaje ganador de la batalla.
- **d_winner**: jugador ganador del duelo.
- **t_winner**: equipo ganador del duelo de equipo en caso de eventos de tipo team_tournament.
- **event_type**: tipo de evento. Puede ser: tournament, league, team_tournament o special_tournament.

### Filas v2

- Cada fila representa un round.
- Cada fila contiene los resultados de un round para ambos jugadores.

### Aclaraciones v2

- Los ganadores de round, batalla y duelo son hechos primarios nunca se deben inferir.
- El tipo de evento está explícito.
- La franquicia del juego está explícita.
- No existe el resultado de round "0".
