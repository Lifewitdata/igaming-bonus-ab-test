"""Interactive Streamlit dashboard for the bonus A/B test results.

Run with:
    streamlit run dashboard/app.py

Lets a stakeholder explore the funnel, significance tests, ROI, and
segmentation without touching code or notebooks -- the kind of
self-serve view Product/Marketing/Ops would actually use.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import polars as pl
import streamlit as st

# Make the src/ package importable when run directly via `streamlit run`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bonus_ab_test.funnel import funnel_by_group, segment_lift  # noqa: E402
from bonus_ab_test.roi import compute_roi  # noqa: E402
from bonus_ab_test.stats_tests import two_proportion_ztest, welch_ttest  # noqa: E402

st.set_page_config(page_title="Bonus A/B Test Dashboard", layout="wide")

DEFAULT_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "ab_test_players.parquet"


@st.cache_data
def load_data(path: str) -> pl.DataFrame:
    if path.endswith(".parquet"):
        return pl.read_parquet(path)
    return pl.read_csv(path, try_parse_dates=True)


def main() -> None:
    st.title("🎰 Bonus A/B Test — iGaming Product Analytics")
    st.caption(
        "First-deposit bonus (100% match, capped at $50) tested against a "
        "no-bonus control group. Built with Polars for the data pipeline."
    )

    with st.sidebar:
        st.header("Data source")
        data_path = st.text_input("Dataset path (.parquet or .csv)", value=str(DEFAULT_DATA_PATH))
        if not Path(data_path).exists():
            st.warning(
                "File not found. Generate it first:\n\n"
                "`bonus-ab-test simulate --out data/ab_test_players.parquet`"
            )
            st.stop()

    df = load_data(data_path)
    st.sidebar.success(f"Loaded {df.height:,} rows")

    with st.sidebar:
        st.header("Filters")
        countries = sorted(df["country"].unique().to_list())
        verticals = sorted(df["vertical"].unique().to_list())
        selected_countries = st.multiselect("Country", countries, default=countries)
        selected_verticals = st.multiselect("Vertical", verticals, default=verticals)

    filtered = df.filter(
        pl.col("country").is_in(selected_countries) & pl.col("vertical").is_in(selected_verticals)
    )

    funnel = funnel_by_group(filtered)
    if funnel.height < 2:
        st.error("Not enough data in both groups for the selected filters.")
        st.stop()

    ctrl = funnel.filter(pl.col("group") == "control").row(0, named=True)
    trt = funnel.filter(pl.col("group") == "treatment").row(0, named=True)

    # --- KPI row -------------------------------------------------------
    st.subheader("Funnel KPIs")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Signup → Deposit",
        f"{trt['signup_to_deposit_rate']:.2%}",
        f"{(trt['signup_to_deposit_rate'] - ctrl['signup_to_deposit_rate']):+.2%} vs control",
    )
    c2.metric(
        "Repeat Deposit (30d)",
        f"{trt['repeat_deposit_rate']:.2%}",
        f"{(trt['repeat_deposit_rate'] - ctrl['repeat_deposit_rate']):+.2%} vs control",
    )
    c3.metric(
        "Avg First Deposit",
        f"${trt['avg_first_deposit']:.2f}",
        f"{(trt['avg_first_deposit'] - ctrl['avg_first_deposit']):+.2f} vs control",
    )
    roi_result = compute_roi(
        control_total_volume=ctrl["total_ltv_30d"],
        control_signups=ctrl["signups"],
        treatment_total_volume=trt["total_ltv_30d"],
        treatment_signups=trt["signups"],
        treatment_total_bonus_cost=trt["total_bonus_cost"],
    )
    c4.metric("Bonus ROI", f"{roi_result.roi:.2f}x", "incremental $ per $1 of bonus")

    # --- Funnel chart ----------------------------------------------------
    st.subheader("Funnel: Control vs Treatment")
    funnel_pd = funnel.select(
        ["group", "signups", "deposits", "bets", "repeat_deposits"]
    ).to_pandas().set_index("group").T
    st.bar_chart(funnel_pd)

    # --- Significance ------------------------------------------------
    st.subheader("Statistical Significance")
    deposit_test = two_proportion_ztest(ctrl["deposits"], ctrl["signups"], trt["deposits"], trt["signups"])
    repeat_test = two_proportion_ztest(ctrl["repeat_deposits"], ctrl["deposits"], trt["repeat_deposits"], trt["deposits"])

    ctrl_amt = filtered.filter((pl.col("group") == "control") & pl.col("reached_deposit"))["first_deposit_amount"].to_numpy()
    trt_amt = filtered.filter((pl.col("group") == "treatment") & pl.col("reached_deposit"))["first_deposit_amount"].to_numpy()
    amount_test = welch_ttest(trt_amt, ctrl_amt)

    sig_df = pd.DataFrame(
        [
            {
                "Metric": "Signup → Deposit",
                "Control": f"{deposit_test.p_control:.2%}",
                "Treatment": f"{deposit_test.p_treatment:.2%}",
                "Lift": f"{deposit_test.absolute_lift:+.2%}",
                "p-value": f"{deposit_test.p_value:.2e}",
                "Significant?": "✅" if deposit_test.significant else "❌",
            },
            {
                "Metric": "Repeat Deposit (30d)",
                "Control": f"{repeat_test.p_control:.2%}",
                "Treatment": f"{repeat_test.p_treatment:.2%}",
                "Lift": f"{repeat_test.absolute_lift:+.2%}",
                "p-value": f"{repeat_test.p_value:.2e}",
                "Significant?": "✅" if repeat_test.significant else "❌",
            },
            {
                "Metric": "Avg First Deposit",
                "Control": f"${amount_test.mean_control:.2f}",
                "Treatment": f"${amount_test.mean_treatment:.2f}",
                "Lift": f"${amount_test.difference:+.2f}",
                "p-value": f"{amount_test.p_value:.2e}",
                "Significant?": "✅" if amount_test.significant else "❌",
            },
        ]
    )
    st.dataframe(sig_df, use_container_width=True, hide_index=True)

    # --- ROI --------------------------------------------------------
    st.subheader("Bonus ROI")
    r1, r2, r3 = st.columns(3)
    r1.metric("Total bonus cost", f"${roi_result.total_bonus_cost:,.0f}")
    r2.metric("Incremental 30d volume", f"${roi_result.incremental_volume:,.0f}")
    r3.metric("ROI", f"{roi_result.roi:.2f}x")

    significant = deposit_test.significant and repeat_test.significant
    recommendation = roi_result.recommendation(significant_lift=significant)
    if roi_result.roi >= 1.0 and significant:
        st.success(recommendation)
    else:
        st.warning(recommendation)

    # --- Segmentation --------------------------------------------------
    st.subheader("Segmentation: Signup → Deposit Lift")
    seg_dim = st.selectbox("Segment by", ["country", "device", "vertical", "channel"])
    seg = segment_lift(filtered, seg_dim).sort("lift_pp", descending=True).to_pandas()
    st.bar_chart(seg.set_index(seg_dim)["lift_pp"])
    st.dataframe(seg, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
