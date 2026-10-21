# Optional ClickHouse route
The default working project uses DuckDB SQL and Streamlit, without AWS credentials.
ClickHouse scripts are supplied but have not been executed against a ClickHouse server.
Do not describe the DuckDB timing results as ClickHouse benchmarks.

After `python scripts/run_sql.py`, install a ClickHouse client/server and run from the repo root:
```bash
clickhouse-client --multiquery < sql/clickhouse_schema.sql
clickhouse-client --query "INSERT INTO gaming_portfolio.players FORMAT CSVWithNames" < data/players.csv
clickhouse-client --query "INSERT INTO gaming_portfolio.settlements FORMAT CSVWithNames" < data/settlements.csv
clickhouse-client --query "INSERT INTO gaming_portfolio.bonuses FORMAT CSVWithNames" < data/bonuses.csv
clickhouse-client --database gaming_portfolio < sql/player_metrics.sql
```
Use an empty dedicated database for each load: repeated INSERTs duplicate rows.
Credentials belong in the client's secure configuration, never in Git.
`player_metrics.sql` uses pre-aggregated left joins. Materialize its SELECT as
`gaming_portfolio.player_metrics` before running `cohort_trends.sql`.
Validate row counts, unique player IDs, GGR and contribution against outputs/gaming_kpis.csv.
Capture EXPLAIN and system.query_log read_rows, read_bytes, query_duration_ms and memory_usage
before making ClickHouse performance claims. Sorting keys are candidates, not proven optimizations.

References: https://clickhouse.com/docs/reference/functions/window-functions
and https://clickhouse.com/docs/reference/engines/table-engines/mergetree-family/mergetree
