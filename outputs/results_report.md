# Bonus experiment: gaming revenue readout
Synthetic data; 3,000,000 fully observed assigned players. No real business impact claimed.

## Decision
DO NOT ROLL OUT: contribution after bonus costs declines.

Primary metric: 30-day contribution per assigned player (GGR minus bonus expense).
Treatment minus control: $-15.285; 95% CI [$-15.360, $-15.211]; p=0.
SRM p=0.2539. Net incremental bonus ROI: -0.9619247480645462 (ratio; undefined when incremental cost is not positive).

## Group KPIs
| group     |   players |   stakes_30d |    wins_30d |     ggr_30d |   bonus_cost |   contribution_30d |   bet_count_30d |   active_players |   d7_retention |   d30_retention |      rtp |
|:----------|----------:|-------------:|------------:|------------:|-------------:|-------------------:|----------------:|-----------------:|---------------:|----------------:|---------:|
| control   |   1499012 |  5.68093e+07 | 5.34205e+07 | 3.38876e+06 |  0           |        3.38876e+06 |        17046230 |           473689 |      0.0947984 |       0.0472938 | 0.940349 |
| treatment |   1500988 |  7.24767e+07 | 6.81754e+07 | 4.30138e+06 |  2.38515e+07 |       -1.95501e+07 |        19393418 |           538863 |      0.111249  |       0.055736  | 0.940652 |

## Funnel
| group     |   signups |   deposits |   bets |   repeat_deposits |   avg_first_deposit |   total_bonus_cost |   total_ltv_30d |   signup_to_deposit_rate |   deposit_to_bet_rate |   repeat_deposit_rate |
|:----------|----------:|-----------:|-------:|------------------:|--------------------:|-------------------:|----------------:|-------------------------:|----------------------:|----------------------:|
| control   |   1499012 |     544129 | 473689 |            159658 |             45.0052 |        0           |     2.83859e+07 |                 0.362992 |              0.870545 |              0.293419 |
| treatment |   1500988 |     612024 | 538863 |            213178 |             52.0389 |        2.38515e+07 |     3.70528e+07 |                 0.407747 |              0.880461 |              0.348316 |

## Interpretation and limitations
Deposits are not revenue. GGR = settled stakes minus winnings; contribution deducts bonus expense but excludes taxes, provider fees and operating costs. Net ROI = incremental contribution / incremental bonus cost, normalized to the treatment population.
All assigned players, including non-depositors, remain in the primary analysis. Depositor-only comparisons are descriptive because deposit is affected by treatment.
Secondary retention/conversion tests use Holm adjustment; see experiment_results.json. Do not stop early on significance. Segment findings generate hypotheses, not rollout authorization.
All 30-day outcomes are simulated after signup; signup-cohort trends are not calendar-day revenue. Review revenue and retention guardrails before a real rollout.
