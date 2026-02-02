SELECT
    -- Season / Event
    s.id                    AS season_id,
    s.name                  AS season_name,

    e.id                    AS event_id,
    e."order"               AS event_order,
    e.event_date            AS event_date,

    -- Duel / Battle
    d.id                    AS duel_id,
    d."order"               AS duel_order,

    b.id                    AS battle_id,
    b."order"               AS battle_order,

    -- Round
    r.id                    AS round_id,
    r."order"               AS round_order,

    -- Player
    p.id                    AS player_id,
    p.nickname              AS player_nickname,
    ctry.iso_code           AS player_country,

    -- Position in battle
    bp.position             AS player_position,

    -- Team (nullable)
    t.id                    AS team_id,
    t.name                  AS team_name,

    -- Character
    ci.name                 AS character_name,
    f.name                  AS character_franchise,

    -- Game context
    g.name                  AS game_name,
    gvp.version             AS game_version,
    plat.name               AS platform,

    -- Stage
    st.name                 AS stage_name,

    -- Result
    rr.result_code          AS round_result,

    -- Opponent result
    rr_opp.result_code      AS opponent_round_result,

    -- Helper
    CASE
        WHEN rr.result_code = '0' THEN 0
        ELSE 1
    END AS round_played

FROM rounds r

JOIN battles b ON b.id = r.battle_id
JOIN duels d   ON d.id = b.duel_id
JOIN events e  ON e.id = d.event_id
JOIN seasons s ON s.id = e.season_id

JOIN stages st ON st.id = b.stage_id

JOIN game_version_platforms gvp
  ON gvp.id = st.game_version_platform_id

JOIN games g
  ON g.id = gvp.game_id

JOIN franchises f
  ON f.id = g.franchise_id

JOIN platforms plat
  ON plat.id = gvp.platform_id

JOIN round_results rr
  ON rr.round_id = r.id

JOIN players p
  ON p.id = rr.player_id

JOIN countries ctry
  ON ctry.id = p.country_id

JOIN battle_participants bp
  ON bp.battle_id = b.id
 AND bp.player_id = p.id

LEFT JOIN duel_teams dt
  ON dt.id = bp.duel_team_id

LEFT JOIN teams t
  ON t.id = dt.team_id

JOIN game_characters gc
  ON gc.id = bp.game_character_id

JOIN character_identities ci
  ON ci.id = gc.character_identity_id

-- Opponent round result (same round, other player)
JOIN round_results rr_opp
  ON rr_opp.round_id = r.id
 AND rr_opp.player_id <> rr.player_id

ORDER BY
    s.id,
    e."order",
    d."order",
    b."order",
    r."order",
    bp.position;