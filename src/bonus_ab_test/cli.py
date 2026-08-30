"""Command-line interface for the bonus A/B test toolkit.

    bonus-ab-test simulate --n-players 3000000 --out data/ab_test_players.parquet
    bonus-ab-test analyze --data data/ab_test_players.parquet --out outputs/
"""

from __future__ import annotations

import logging
from pathlib import Path

import click
import polars as pl

from bonus_ab_test.config import SimulationConfig
from bonus_ab_test.report import build_report
from bonus_ab_test.simulate import simulate_players

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@click.group()
def cli() -> None:
    """Bonus A/B test analytics toolkit."""


@cli.command()
@click.option("--n-players", default=3_000_000, show_default=True, type=int)
@click.option("--seed", default=42, show_default=True, type=int)
@click.option("--out", default="data/ab_test_players.parquet", show_default=True, type=click.Path())
def simulate(n_players: int, seed: int, out: str) -> None:
    """Generate the simulated A/B test dataset and write it to Parquet."""
    cfg = SimulationConfig(n_players=n_players, seed=seed)
    df = simulate_players(cfg)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out)
    click.echo(f"Wrote {df.height:,} rows -> {out}")


@cli.command()
@click.option("--data", default="data/ab_test_players.parquet", show_default=True, type=click.Path(exists=True))
@click.option("--out", default="outputs", show_default=True, type=click.Path())
def analyze(data: str, out: str) -> None:
    """Run the full funnel / significance / ROI / segmentation report."""
    df = pl.read_parquet(data) if data.endswith(".parquet") else pl.read_csv(data)
    report_path = build_report(df, out)
    click.echo(f"Report written to {report_path}")


@cli.command()
@click.option("--n-players", default=3_000_000, show_default=True, type=int)
@click.option("--seed", default=42, show_default=True, type=int)
@click.option("--data-out", default="data/ab_test_players.parquet", show_default=True, type=click.Path())
@click.option("--report-out", default="outputs", show_default=True, type=click.Path())
def run(n_players: int, seed: int, data_out: str, report_out: str) -> None:
    """Simulate + analyze in one step."""
    cfg = SimulationConfig(n_players=n_players, seed=seed)
    df = simulate_players(cfg)
    Path(data_out).parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(data_out)
    click.echo(f"Wrote {df.height:,} rows -> {data_out}")
    report_path = build_report(df, report_out)
    click.echo(f"Report written to {report_path}")


if __name__ == "__main__":
    cli()
