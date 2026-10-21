-- Aggregate each fact before joining to prevent bonus/settlement fanout.
WITH settled AS (
 SELECT player_id, SUM(stakes) stakes, SUM(wins) wins, SUM(bet_count) bet_count
 FROM settlements GROUP BY player_id
), costs AS (
 SELECT player_id, SUM(bonus_cost) bonus_cost FROM bonuses GROUP BY player_id
)
SELECT p.player_id,p.signup_date,p.country,p.vertical,p.variant,
 COALESCE(s.stakes,0) stakes,COALESCE(s.wins,0) wins,
 COALESCE(s.stakes,0)-COALESCE(s.wins,0) ggr,
 COALESCE(b.bonus_cost,0) bonus_cost,
 COALESCE(s.stakes,0)-COALESCE(s.wins,0)-COALESCE(b.bonus_cost,0) contribution,
 COALESCE(s.bet_count,0) bet_count
FROM players p LEFT JOIN settled s ON p.player_id=s.player_id
LEFT JOIN costs b ON p.player_id=b.player_id
