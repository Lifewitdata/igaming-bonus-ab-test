"""Run: streamlit run dashboard/app.py"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import polars as pl
import streamlit as st
from bonus_ab_test.config import SimulationConfig
from bonus_ab_test.simulate import simulate_players
from bonus_ab_test.gaming import validate, gaming_summary, experiment_readout
from bonus_ab_test.funnel import funnel_by_group, segment_lift

st.set_page_config(page_title="Gaming performance & experiments",layout="wide")
ROOT=Path(__file__).resolve().parents[1]
@st.cache_data
def demo(): return simulate_players(SimulationConfig(n_players=50000))
@st.cache_data
def read_file(path,mtime): return pl.read_parquet(path)

def main():
    st.title("Gaming performance & bonus experiment")
    st.caption("Synthetic portfolio data • 30-day matured player outcomes • USD • Streamlit")
    p=ROOT/"data/ab_test_players.parquet"
    df=read_file(str(p),p.stat().st_mtime_ns) if p.exists() else demo()
    st.sidebar.info(f"{df.height:,} players • {'local dataset' if p.exists() else 'built-in demo'}")
    try: quality=validate(df)
    except ValueError as e: st.error(str(e));st.stop()
    country=st.sidebar.multiselect("Country",sorted(df["country"].unique()),default=sorted(df["country"].unique()))
    vertical=st.sidebar.multiselect("Game vertical",sorted(df["vertical"].unique()),default=sorted(df["vertical"].unique()))
    dates=st.sidebar.date_input("Signup cohort",value=(df["signup_date"].min(),df["signup_date"].max()))
    if len(dates)!=2: st.info("Choose both cohort dates.");st.stop()
    f=df.filter(pl.col("country").is_in(country)&pl.col("vertical").is_in(vertical)&pl.col("signup_date").is_between(*dates))
    if f.is_empty():st.warning("No players match these filters.");st.stop()
    totals=gaming_summary(f).sum().row(0,named=True)
    c=st.columns(4)
    c[0].metric("GGR",f"${totals['ggr_30d']:,.0f}")
    c[1].metric("RTP",f"{totals['wins_30d']/totals['stakes_30d']:.2%}" if totals['stakes_30d'] else "N/A")
    c[2].metric("Settled bet volume",f"${totals['stakes_30d']:,.0f}")
    c[3].metric("Contribution after bonuses",f"${totals['contribution_30d']:,.0f}")
    overview,experiment,qualitytab=st.tabs(["Performance","Experiment decision","Data quality & definitions"])
    with overview:
        st.dataframe(gaming_summary(f),hide_index=True)
        st.caption("D7/D30: exact-day active players divided by all assigned players. Bet volume is stake value; bet count is separate.")
        trend=gaming_summary(f,"signup_date").to_pandas().set_index("signup_date")
        st.subheader("30-day outcomes by signup cohort")
        st.line_chart(trend[["ggr_30d","contribution_30d"]])
        st.dataframe(funnel_by_group(f),hide_index=True)
        st.download_button("Download filtered KPIs",gaming_summary(f).write_csv(),"gaming_kpis.csv")
    with experiment:
        st.info("The decision below always uses the full randomized population. Filters apply only to exploratory charts, avoiding post-hoc segment rollout claims.")
        result=experiment_readout(df)
        st.metric("Contribution effect per assigned player",f"${result['effect']:+.2f}")
        st.write(f"95% CI: ${result['low']:.2f} to ${result['high']:.2f}; p={result['p']:.3g}; SRM p={result['srm_p']:.3g}")
        st.write("Net incremental bonus ROI:",f"{result['net_roi']:.2%}" if result['net_roi'] is not None else "Undefined: no incremental bonus cost")
        st.warning(result['decision'])
        st.dataframe(result['secondary'],hide_index=True)
        st.caption("Secondary p-values use Holm adjustment. No early stopping: wait for the fixed sample and full 30-day follow-up. Contribution excludes tax, provider fees and other operating costs.")
        dim=st.selectbox("Explore conversion lift",["country","device","vertical","channel"])
        if f["group"].n_unique()==2: st.dataframe(segment_lift(f,dim),hide_index=True)
    with qualitytab:
        st.json(quality)
        st.write("GGR = settled stakes − total winnings (including returned stake). RTP = total winnings / total stakes. Contribution = GGR − bonus expense. Deposits are not revenue.")
        st.write("All players have a simulated full follow-up. These are player-level settlement totals, not a transaction ledger or an operational daily gaming feed.")
        st.write("Owner: project maintainer. Rebuild after source changes, run validation and tests before release, review failed checks before publishing.")
if __name__=="__main__": main()
