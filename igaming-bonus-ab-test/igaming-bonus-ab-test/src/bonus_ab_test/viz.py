"""Matplotlib chart builders for the funnel / segmentation results."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import polars as pl

plt.style.use("seaborn-v0_8-whitegrid")

CONTROL_COLOR = "#6b7280"
TREATMENT_COLOR = "#2563eb"


def plot_funnel_comparison(funnel: pl.DataFrame, out_path: str | Path) -> Path:
    stages = ["signups", "deposits", "bets", "repeat_deposits"]
    ctrl = funnel.filter(pl.col("group") == "control").row(0, named=True)
    trt = funnel.filter(pl.col("group") == "treatment").row(0, named=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(stages))
    width = 0.35
    ax.bar(x - width / 2, [ctrl[s] for s in stages], width, label="Control", color=CONTROL_COLOR)
    ax.bar(x + width / 2, [trt[s] for s in stages], width, label="Treatment (bonus)", color=TREATMENT_COLOR)
    ax.set_xticks(x)
    ax.set_xticklabels(["Signup", "Deposit", "Bet", "Repeat Deposit (30d)"])
    ax.set_ylabel("Players")
    ax.set_title("Funnel by Group: Control vs Treatment")
    ax.legend()
    fig.tight_layout()
    out_path = Path(out_path)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_conversion_rates(funnel: pl.DataFrame, out_path: str | Path) -> Path:
    rates = ["signup_to_deposit_rate", "deposit_to_bet_rate", "repeat_deposit_rate"]
    ctrl = funnel.filter(pl.col("group") == "control").row(0, named=True)
    trt = funnel.filter(pl.col("group") == "treatment").row(0, named=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(rates))
    width = 0.35
    ax.bar(x - width / 2, [ctrl[r] * 100 for r in rates], width, label="Control", color=CONTROL_COLOR)
    ax.bar(x + width / 2, [trt[r] * 100 for r in rates], width, label="Treatment (bonus)", color=TREATMENT_COLOR)
    ax.set_xticks(x)
    ax.set_xticklabels(["Signup\u2192Deposit", "Deposit\u2192Bet", "Repeat Deposit"])
    ax.set_ylabel("Conversion Rate (%)")
    ax.set_title("Conversion Rates: Control vs Treatment")
    ax.legend()
    fig.tight_layout()
    out_path = Path(out_path)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_segment_lift(seg_df: pl.DataFrame, segment_col: str, title: str, out_path: str | Path) -> Path:
    pdf = seg_df.sort("lift_pp", descending=True).to_pandas()
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = [TREATMENT_COLOR if v > 0 else "#dc2626" for v in pdf["lift_pp"]]
    ax.barh(pdf[segment_col], pdf["lift_pp"] * 100, color=colors)
    ax.set_xlabel("Signup\u2192Deposit Lift (percentage points)")
    ax.set_title(title)
    ax.axvline(0, color="black", linewidth=0.8)
    fig.tight_layout()
    out_path = Path(out_path)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path
