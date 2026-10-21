"""Execute SQL, reconcile with source, benchmark raw joins vs materialized metrics."""
import json,time,statistics
from pathlib import Path
import duckdb
import polars as pl
ROOT=Path(__file__).resolve().parents[1]
data=ROOT/"data/ab_test_players.parquet"
if not data.exists(): raise SystemExit("Run bonus-ab-test run first.")
df=pl.read_parquet(data)
from bonus_ab_test.gaming import validate
validate(df)
con=duckdb.connect(str(ROOT/"data/analytics.duckdb"))
con.register("source_players",df.to_arrow())
con.execute('CREATE OR REPLACE TABLE players AS SELECT player_id,signup_date,country,vertical,"group" AS variant FROM source_players')
con.execute('CREATE OR REPLACE TABLE settlements AS SELECT player_id,stakes_30d stakes,wins_30d wins,bet_count_30d bet_count FROM source_players WHERE reached_bet')
con.execute('CREATE OR REPLACE TABLE bonuses AS SELECT player_id,bonus_cost FROM source_players WHERE bonus_cost>0')
query=(ROOT/"sql/player_metrics.sql").read_text()
con.execute("CREATE OR REPLACE TABLE player_metrics AS "+query)
checks=con.execute("SELECT count(*),sum(ggr),sum(contribution) FROM player_metrics").fetchone()
assert checks[0]==df.height
assert abs(checks[1]-df['ggr_30d'].sum())<.01
assert abs(checks[2]-df['contribution_30d'].sum())<.01
out=ROOT/"outputs";out.mkdir(exist_ok=True)
con.execute((ROOT/"sql/cohort_trends.sql").read_text()).fetchdf().to_csv(out/"sql_cohort_trends.csv",index=False)
raw="SELECT variant,sum(contribution) FROM ("+query+") GROUP BY variant"
fast="SELECT variant,sum(contribution) FROM player_metrics GROUP BY variant"
bench={}
for name,q in [('raw_join',raw),('materialized',fast)]:
 con.execute(q).fetchall() # warm up
 timings=[]
 for _ in range(5):
  start=time.perf_counter();con.execute(q).fetchall();timings.append(time.perf_counter()-start)
 bench[name]={'median_seconds':statistics.median(timings),'runs':timings}
 (out/(name+'_explain.txt')).write_text(str(con.execute('EXPLAIN ANALYZE '+q).fetchall()))
a=sorted(con.execute(raw).fetchall());b=sorted(con.execute(fast).fetchall())
assert all(x[0]==y[0] and abs(x[1]-y[1])<.01 for x,y in zip(a,b))
bench.update(engine='DuckDB '+duckdb.__version__,players=df.height,checks='passed',note='Local warm-cache benchmark; not ClickHouse performance. Materialization has build/storage costs.')
(out/'sql_validation.json').write_text(json.dumps(bench,indent=2));print(json.dumps(bench,indent=2))
for table in ['players','settlements','bonuses']:
 con.execute('SELECT * FROM '+table).fetchdf().to_csv(ROOT/'data'/f'{table}.csv',index=False)
con.close()
