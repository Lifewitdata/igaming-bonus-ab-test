# Experiment contract
Decision: does a first-deposit bonus increase 30-day contribution per assigned player?
Randomization: player, 50/50. Primary: GGR minus bonus expense per assigned player,
including zero outcomes. Two-sided alpha .05, fixed horizon; no repeated significance stopping.
For a real launch, specify a meaningful dollar MDE and estimate the primary metric variance
from an independent pilot, then size at 80% power before assignment. The existing binary
sample-size helper applies to conversion, not monetary contribution.
Approximate primary sizing per arm: 2*(z_.975+z_.80)^2 * pilot_variance / dollar_MDE^2.
Wait until every enrolled player completes 30 days; pipeline delay is additional.
Secondary family: deposit conversion, exact-day D7 and D30 retention; Holm adjustment.
SRM threshold .01 blocks rollout pending assignment/tracking investigation. Welch intervals
use independent player totals; millions of bets do not mean millions of independent players.
Guardrails: retention, payment errors, responsible-gaming harm signals and operational costs.
Only retention is simulated here; absent guardrails mean no unconditional rollout approval.
Filtered segments are exploratory. Follow-up experiments require new hypotheses and sizing.
Simulator outcomes are deliberately generated, not evidence of real casino profitability.
