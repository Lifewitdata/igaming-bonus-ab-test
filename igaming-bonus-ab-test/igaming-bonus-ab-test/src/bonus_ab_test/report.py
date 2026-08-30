"""Builds the end-to-end markdown results report from a player-level DataFrame."""

from __future__ import annotations

import logging
from pathlib import Path

import polars as pl

from bonus_ab_test import viz
from bonus_ab_test.funnel import funnel_by_group, segment_lift
from bonus_ab_test.roi import compute_roi
from bonus_ab_test.stats_tests import two_proportion_ztest, welch_ttest

logger = logging.getLogger(__name__)

SEGMENT_COLUMNS = ["country", "device", "vertical", "channel"]


def build_report(df: pl.DataFrame, output_dir: str | Path) -> Path:
    """Run the full analysis and write a markdown report + charts to `output_dir`.

    Returns the path to the written report.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []

    def log(line: str = "") -> None:
        lines.append(line)

    log("# Bonus A/B Test — Results Report\n")
    log(f"Dataset: {df.height:,} players\n")

    # 1. Funnel
    funnel = funnel_by_group(df)
    ctrl = funnel.filter(pl.col("group") == "control").row(0, named=True)
    trt = funnel.filter(pl.col("group") == "treatment").row(0, named=True)

    log("## 1. Funnel by Group\n")
    log(
        funnel.select(
            [
                "group", "signups", "deposits", "signup_to_deposit_rate",
                "deposit_to_bet_rate", "repeat_deposit_rate", "avg_first_deposit",
            ]
        ).to_pandas().to_markdown(index=False)
    )
    log()

    # 2. Significance
    log("## 2. Statistical Significance\n")

    deposit_test = two_proportion_ztest(ctrl["deposits"], ctrl["signups"], trt["deposits"], trt["signups"])
    log("**Signup \u2192 Deposit conversion**")
    log(f"- Control: {deposit_test.p_control:.4%}  |  Treatment: {deposit_test.p_treatment:.4%}")
    log(f"- Absolute lift: {deposit_test.absolute_lift:+.4%} (relative: {deposit_test.relative_lift:+.2%})")
    log(
        f"- z = {deposit_test.z_stat:.2f}, p-value = {deposit_test.p_value:.2e}, "
        f"95% CI on lift: [{deposit_test.ci_low:.4%}, {deposit_test.ci_high:.4%}]"
    )
    log(f"- **{'Statistically significant' if deposit_test.significant else 'Not significant'} at \u03b1 = 0.05**\n")

    repeat_test = two_proportion_ztest(
        ctrl["repeat_deposits"], ctrl["deposits"], trt["repeat_deposits"], trt["deposits"]
    )
    log("**Repeat-deposit rate within 30d (among depositors)**")
    log(f"- Control: {repeat_test.p_control:.4%}  |  Treatment: {repeat_test.p_treatment:.4%}")
    log(f"- Absolute lift: {repeat_test.absolute_lift:+.4%} (relative: {repeat_test.relative_lift:+.2%})")
    log(
        f"- z = {repeat_test.z_stat:.2f}, p-value = {repeat_test.p_value:.2e}, "
        f"95% CI on lift: [{repeat_test.ci_low:.4%}, {repeat_test.ci_high:.4%}]"
    )
    log(f"- **{'Statistically significant' if repeat_test.significant else 'Not significant'} at \u03b1 = 0.05**\n")

    ctrl_amt = df.filter((pl.col("group") == "control") & pl.col("reached_deposit"))["first_deposit_amount"].to_numpy()
    trt_amt = df.filter((pl.col("group") == "treatment") & pl.col("reached_deposit"))["first_deposit_amount"].to_numpy()
    amount_test = welch_ttest(trt_amt, ctrl_amt)
    log("**First deposit amount (among depositors)**")
    log(f"- Control mean: ${amount_test.mean_control:.2f}  |  Treatment mean: ${amount_test.mean_treatment:.2f}")
    log(f"- Difference: ${amount_test.difference:+.2f}")
    log(f"- t = {amount_test.t_stat:.2f}, p-value = {amount_test.p_value:.2e}")
    log(f"- **{'Statistically significant' if amount_test.significant else 'Not significant'} at \u03b1 = 0.05**\n")

    # 3. ROI
    log("## 3. Bonus ROI\n")
    roi_result = compute_roi(
        control_total_volume=ctrl["total_ltv_30d"],
        control_signups=ctrl["signups"],
        treatment_total_volume=trt["total_ltv_30d"],
        treatment_signups=trt["signups"],
        treatment_total_bonus_cost=trt["total_bonus_cost"],
    )
    log(f"- Total bonus paid out (treatment group): **${roi_result.total_bonus_cost:,.2f}**")
    log(f"- Treatment group total 30-day deposit volume (LTV proxy): ${roi_result.treatment_total_volume:,.2f}")
    log(f"- Expected volume at control's conversion/spend rate: ${roi_result.expected_volume_at_control_rate:,.2f}")
    log(f"- **Estimated incremental 30-day deposit volume: ${roi_result.incremental_volume:,.2f}**")
    log(f"- **ROI (incremental volume / bonus cost): {roi_result.roi:.2f}x**\n")

    # 4. Segmentation
    log("## 4. Segmentation: Signup \u2192 Deposit Lift by Segment\n")
    segment_frames: dict[str, pl.DataFrame] = {}
    for col in SEGMENT_COLUMNS:
        seg = segment_lift(df, col)
        segment_frames[col] = seg
        log(f"**By {col}:**")
        log(seg.to_pandas().to_markdown(index=False, floatfmt=".4f"))
        log()

    # 5. Charts
    log("## 5. Charts\n")
    viz.plot_funnel_comparison(funnel, output_dir / "funnel_comparison.png")
    viz.plot_conversion_rates(funnel, output_dir / "conversion_rates.png")
    viz.plot_segment_lift(segment_frames["country"], "country", "Bonus Lift by Country", output_dir / "lift_by_country.png")
    log("Saved to `outputs/`: `funnel_comparison.png`, `conversion_rates.png`, `lift_by_country.png`\n")

    # 6. Recommendation
    log("## 6. Recommendation\n")
    log(roi_result.recommendation(significant_lift=deposit_test.significant and repeat_test.significant))

    report_path = output_dir / "results_report.md"
    report_path.write_text("\n".join(lines))
    logger.info("Report written to %s", report_path)
    return report_path
