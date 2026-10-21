# iGaming Bonus Experiment — SQL, Python and Streamlit

Synthetic casino/sportsbook portfolio project. Evaluate whether a deposit bonus
improves **30-day gaming contribution**, not just deposit conversion.
No AWS or QuickSight login is needed. The dashboard has a built-in 50,000-player demo.

## Run
```bash
pip install -e ".[dev]"
streamlit run dashboard/app.py
```
For the full reproducible workflow:
```bash
bonus-ab-test run --n-players 3000000
python scripts/run_sql.py
pytest -q
streamlit run dashboard/app.py
```
The default seed is 42. Data generation includes the original deposit funnel plus
synthetic settled 30-day stakes, winnings, bet counts and exact-day retention.
All players have full follow-up, including late signups. This is a player-level
settlement summary, not a transaction-level ledger or production daily feed.

## What changed
- Streamlit retained, with GGR, RTP, bet volume/count, active players, retention,
  contribution, cohort filters, CSV export and a full-population experiment decision.
- Deposit volume is no longer called revenue ROI. GGR = stakes minus winnings;
  contribution = GGR minus bonus expense (before taxes, provider fees and overhead).
- Primary effect is treatment minus control contribution per **assigned player**,
  with a Welch confidence interval, SRM check and conservative decision.
- Net incremental bonus ROI = incremental contribution / incremental bonus expense.
- Secondary metrics receive Holm adjustment; filtered segment views are exploratory.
- SQL pre-aggregates financial facts before joining to avoid double-counting;
  LAG, rolling windows and DENSE_RANK support cohort analysis.
- DuckDB executes SQL locally. The benchmark measures raw joins versus a materialized
  player table and reconciles totals to Python. ClickHouse deployment SQL is optional
  and unverified on a server; see docs/clickhouse.md.

## Review
| File | Purpose |
|---|---|
| dashboard/app.py | Working dashboard; no login |
| src/bonus_ab_test/gaming.py | Financial validation, KPIs and experiment inference |
| sql/player_metrics.sql | Pre-aggregation and multi-table joins |
| sql/cohort_trends.sql | Window functions |
| scripts/run_sql.py | SQL execution, reconciliation, timing and exports |
| outputs/results_report.md | Generated decision and limitations |
| outputs/sql_validation.json | Actual local benchmark results |
| docs/experiment_plan.md | Sizing, peeking, multiplicity and guardrails |
| docs/clickhouse.md | Optional migration and validation instructions |

The historical notebook/plots describe the earlier deposit-volume analysis and are
retained only as legacy material. They are not the current revenue readout; use the
CLI report and dashboard. The legacy roi.py API is a deposit-volume ratio and never
authorizes rollout. Do not claim a real uplift or deployed QuickSight/ClickHouse dashboard.

Maintenance: rerun validation, SQL reconciliation and tests after every source/model
change; review failures before refreshing reports. Review dashboard use with stakeholders
and retire unused views. Simulation findings do not justify targeting real players.

MIT license. This project is independent of any casino or employer.
