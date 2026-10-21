"""Decision report using settled gaming revenue rather than deposit volume."""
import json
from pathlib import Path
from bonus_ab_test.gaming import validate,gaming_summary,experiment_readout
from bonus_ab_test.funnel import funnel_by_group

def build_report(df,output_dir):
    p=Path(output_dir);p.mkdir(parents=True,exist_ok=True)
    checks=validate(df); result=experiment_readout(df)
    gaming_summary(df).write_csv(p/"gaming_kpis.csv")
    (p/"experiment_results.json").write_text(json.dumps(result,indent=2))
    (p/"data_quality.json").write_text(json.dumps(checks,indent=2))
    text=f"""# Bonus experiment: gaming revenue readout
Synthetic data; {df.height:,} fully observed assigned players. No real business impact claimed.

## Decision
{result['decision']}

Primary metric: 30-day contribution per assigned player (GGR minus bonus expense).
Treatment minus control: ${result['effect']:.3f}; 95% CI [${result['low']:.3f}, ${result['high']:.3f}]; p={result['p']:.4g}.
SRM p={result['srm_p']:.4g}. Net incremental bonus ROI: {result['net_roi']} (ratio; undefined when incremental cost is not positive).

## Group KPIs
{gaming_summary(df).to_pandas().to_markdown(index=False)}

## Funnel
{funnel_by_group(df).to_pandas().to_markdown(index=False)}

## Interpretation and limitations
Deposits are not revenue. GGR = settled stakes minus winnings; contribution deducts bonus expense but excludes taxes, provider fees and operating costs. Net ROI = incremental contribution / incremental bonus cost, normalized to the treatment population.
All assigned players, including non-depositors, remain in the primary analysis. Depositor-only comparisons are descriptive because deposit is affected by treatment.
Secondary retention/conversion tests use Holm adjustment; see experiment_results.json. Do not stop early on significance. Segment findings generate hypotheses, not rollout authorization.
All 30-day outcomes are simulated after signup; signup-cohort trends are not calendar-day revenue. Review revenue and retention guardrails before a real rollout.
"""
    target=p/"results_report.md";target.write_text(text);return target
