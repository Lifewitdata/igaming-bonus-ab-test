# Validation performed
- Full synthetic pipeline: 3,000,000 players, seed 42.
- 20 tests passed, including Streamlit AppTest default view and empty filters.
- DuckDB SQL reconciliation: player count, GGR and contribution match Python.
- Warm-cache median query time, five runs: raw join 0.09134s; materialized table 0.00419s.
  This excludes materialization cost and is specific to this environment.
- Primary simulated effect: -$15.2855 per assigned player; 95% CI [-15.3601, -15.2109].
- ClickHouse server execution and native browser visual rendering were not performed.
- QuickSight is not required or implemented.
