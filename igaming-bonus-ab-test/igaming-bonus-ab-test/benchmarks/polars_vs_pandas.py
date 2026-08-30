"""Benchmarks the core group-by/aggregation workload in Polars vs Pandas
on the full simulated dataset, to justify the Polars choice with numbers
rather than assertion.

Run: python3 benchmarks/polars_vs_pandas.py [path/to/data.parquet]
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import polars as pl

DEFAULT_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "ab_test_players.parquet"


def polars_run(path: str) -> float:
    t0 = time.perf_counter()
    df = pl.read_parquet(path)
    funnel = (
        df.group_by(["group", "country"])
        .agg(
            [
                pl.len().alias("signups"),
                pl.col("reached_deposit").sum().alias("deposits"),
                pl.col("first_deposit_amount").filter(pl.col("reached_deposit")).mean().alias("avg_deposit"),
            ]
        )
        .with_columns((pl.col("deposits") / pl.col("signups")).alias("rate"))
        .sort(["country", "group"])
    )
    _ = funnel.height
    return time.perf_counter() - t0


def pandas_run(path: str) -> float:
    t0 = time.perf_counter()
    df = pd.read_parquet(path)
    g = df.groupby(["group", "country"])
    funnel = g.agg(signups=("player_id", "size"), deposits=("reached_deposit", "sum"))
    avg_dep = (
        df[df["reached_deposit"]]
        .groupby(["group", "country"])["first_deposit_amount"]
        .mean()
        .rename("avg_deposit")
    )
    funnel = funnel.join(avg_dep)
    funnel["rate"] = funnel["deposits"] / funnel["signups"]
    funnel = funnel.sort_index()
    _ = len(funnel)
    return time.perf_counter() - t0


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else str(DEFAULT_DATA_PATH)
    if not Path(path).exists():
        raise SystemExit(f"Dataset not found at {path}. Run `bonus-ab-test simulate` first.")

    print(f"Benchmarking against {path}\n")
    polars_times = [polars_run(path) for _ in range(3)]
    pandas_times = [pandas_run(path) for _ in range(3)]

    print(f"Polars times (s): {[round(t, 3) for t in polars_times]} -> best: {min(polars_times):.3f}s")
    print(f"Pandas times (s): {[round(t, 3) for t in pandas_times]} -> best: {min(pandas_times):.3f}s")
    print(f"\nPolars speedup: {min(pandas_times) / min(polars_times):.1f}x faster (best of 3)")


if __name__ == "__main__":
    main()
