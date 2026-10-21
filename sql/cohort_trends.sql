-- One row per signup date and arm, not calendar-day betting revenue.
WITH daily AS (
 SELECT signup_date,variant,COUNT(*) players,SUM(ggr) ggr,SUM(contribution) contribution,
 SUM(stakes) stakes,SUM(wins) wins
 FROM player_metrics GROUP BY signup_date,variant
)
SELECT *, wins/NULLIF(stakes,0) rtp,
 LAG(contribution) OVER(PARTITION BY variant ORDER BY signup_date) previous_cohort_contribution,
 SUM(contribution) OVER(PARTITION BY variant ORDER BY signup_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) seven_cohort_contribution,
 DENSE_RANK() OVER(PARTITION BY signup_date ORDER BY contribution DESC) contribution_rank
FROM daily ORDER BY signup_date,variant
