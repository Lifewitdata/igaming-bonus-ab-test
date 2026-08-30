"""Funnel aggregation over the player-level dataset, using Polars."""

from __future__ import annotations

import polars as pl


def funnel_by_group(df: pl.DataFrame, group_col: str = "group") -> pl.DataFrame:
    """Aggregate signup -> deposit -> bet -> repeat-deposit funnel by group.

    Returns one row per group with raw counts, conversion rates at each
    stage, average first deposit, total bonus cost, and total 30-day
    deposit volume (used as an LTV proxy).
    """
    return (
        df.group_by(group_col)
        .agg(
            [
                pl.len().alias("signups"),
                pl.col("reached_deposit").sum().alias("deposits"),
                pl.col("reached_bet").sum().alias("bets"),
                pl.col("repeat_deposit_30d").sum().alias("repeat_deposits"),
                pl.col("first_deposit_amount")
                .filter(pl.col("reached_deposit"))
                .mean()
                .alias("avg_first_deposit"),
                pl.col("bonus_cost").sum().alias("total_bonus_cost"),
                pl.col("ltv_30d").sum().alias("total_ltv_30d"),
            ]
        )
        .with_columns(
            [
                (pl.col("deposits") / pl.col("signups")).alias("signup_to_deposit_rate"),
                (pl.col("bets") / pl.col("deposits")).alias("deposit_to_bet_rate"),
                (pl.col("repeat_deposits") / pl.col("deposits")).alias("repeat_deposit_rate"),
            ]
        )
        .sort(group_col)
    )


def segment_lift(
    df: pl.DataFrame,
    segment_col: str,
    group_col: str = "group",
    outcome_col: str = "reached_deposit",
) -> pl.DataFrame:
    """Signup -> outcome conversion rate lift (treatment - control) by segment.

    `outcome_col` must be a boolean column (default: reached first deposit).
    """
    return (
        df.group_by([segment_col, group_col])
        .agg(
            [
                pl.len().alias("signups"),
                pl.col(outcome_col).sum().alias("conversions"),
            ]
        )
        .with_columns((pl.col("conversions") / pl.col("signups")).alias("rate"))
        .pivot(values="rate", index=segment_col, on=group_col)
        .with_columns((pl.col("treatment") - pl.col("control")).alias("lift_pp"))
        .sort("lift_pp", descending=True)
    )
