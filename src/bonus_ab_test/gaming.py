"""Synthetic settled 30-day gaming ledger and intention-to-treat readout."""
import numpy as np
import polars as pl
from scipy import stats


def add_gaming_outcomes(df, seed=42):
    rng = np.random.default_rng(seed + 100)
    n = df.height
    active = df["reached_bet"].to_numpy()
    treatment = df["group"].to_numpy() == "treatment"
    # Aggregate settled stakes can exceed deposits because balances are recycled.
    stake = np.where(active, rng.gamma(2, 60, n) * (1 + .12*treatment), 0).round(2)
    # Volatile realised payout ratios, including winners with payouts > stakes.
    payout = (stake * rng.gamma(8, .94/8, n)).round(2)
    d7 = active & (rng.random(n) < (.30 + .01*treatment))
    d30 = active & (rng.random(n) < (.15 + .005*treatment))
    return df.with_columns(
        pl.Series("stakes_30d", stake), pl.Series("wins_30d", payout),
        pl.Series("retained_d7", d7), pl.Series("retained_d30", d30),
        pl.Series("bet_count_30d", np.where(active, rng.poisson(35,n)+1, 0)),
    ).with_columns((pl.col("stakes_30d")-pl.col("wins_30d")).alias("ggr_30d")).with_columns(
        (pl.col("ggr_30d")-pl.col("bonus_cost")).alias("contribution_30d"))


def validate(df):
    required = ["player_id", "group", "stakes_30d", "wins_30d", "ggr_30d",
                "bonus_cost", "contribution_30d", "retained_d7", "retained_d30"]
    if not set(required).issubset(df.columns):
        raise ValueError("Old dataset: regenerate with bonus-ab-test simulate.")
    if df.height == 0 or df["player_id"].n_unique() != df.height:
        raise ValueError("Player IDs must be unique and data nonempty.")
    if df.select(required).null_count().row(0) != (0,)*len(required):
        raise ValueError("Missing required values.")
    if set(df["group"].unique()) != {"control", "treatment"}:
        raise ValueError("Both randomized groups are required.")
    for c in ["stakes_30d", "wins_30d", "bonus_cost", "ggr_30d", "contribution_30d"]:
        if not df[c].is_finite().all(): raise ValueError("Non-finite financial value.")
    if df.filter((pl.col("stakes_30d")<0)|(pl.col("wins_30d")<0)|(pl.col("bonus_cost")<0)).height:
        raise ValueError("Negative stakes, winnings or costs.")
    for actual, expected in [("ggr_30d",pl.col("stakes_30d")-pl.col("wins_30d")),
                             ("contribution_30d",pl.col("ggr_30d")-pl.col("bonus_cost"))]:
        if df.filter((pl.col(actual)-expected).abs()>1e-7).height:
            raise ValueError("Financial reconciliation failed.")
    return {"players": df.height, "duplicate_ids": 0, "financial_reconciliation": "passed"}


def mean_effect(control, treatment):
    a,b=np.asarray(control,dtype=float),np.asarray(treatment,dtype=float)
    if min(len(a),len(b))<2: raise ValueError("At least two players per arm required.")
    v1,v2=a.var(ddof=1)/len(a),b.var(ddof=1)/len(b)
    se=np.sqrt(v1+v2); delta=float(b.mean()-a.mean())
    if se == 0: return dict(effect=delta,low=delta,high=delta,p=1. if delta==0 else 0.)
    dof=(v1+v2)**2/(v1*v1/(len(a)-1)+v2*v2/(len(b)-1))
    margin=stats.t.ppf(.975,dof)*se
    return dict(effect=delta,low=float(delta-margin),high=float(delta+margin),
                p=float(2*stats.t.sf(abs(delta/se),dof)))


def holm(pvalues):
    p=np.asarray(pvalues); order=np.argsort(p)
    adjusted=np.empty(len(p));adjusted[order]=np.minimum(1,np.maximum.accumulate(p[order]*(len(p)-np.arange(len(p)))))
    return adjusted.tolist()


def experiment_readout(df):
    validate(df)
    a=df.filter(pl.col("group")=="control"); b=df.filter(pl.col("group")=="treatment")
    result=mean_effect(a["contribution_30d"],b["contribution_30d"])
    srm=float(stats.chisquare([a.height,b.height]).pvalue)
    incremental=result["effect"]*b.height
    extra_cost=float(b["bonus_cost"].sum()-a["bonus_cost"].mean()*b.height)
    result.update(srm_p=srm,incremental_contribution=incremental,
                  net_roi=incremental/extra_cost if extra_cost>0 else None)
    if srm<.01: decision="INVESTIGATE: allocation mismatch; do not make a rollout decision."
    elif result["high"]<0: decision="DO NOT ROLL OUT: contribution after bonus costs declines."
    elif result["low"]>0: decision="Positive contribution signal; review guardrails and operational costs before rollout."
    else: decision="INCONCLUSIVE: the interval includes zero; do not claim a profitable lift."
    result["decision"]=decision
    secondary=[]
    for col in ["reached_deposit","retained_d7","retained_d30"]:
        e=mean_effect(a[col],b[col]); secondary.append({"metric":col,**e})
    for row,p in zip(secondary,holm([x["p"] for x in secondary])): row["holm_p"]=p
    result["secondary"]=secondary
    return result


def gaming_summary(df, by="group"):
    return df.group_by(by).agg(pl.len().alias("players"),
        pl.col("stakes_30d").sum(),pl.col("wins_30d").sum(),pl.col("ggr_30d").sum(),
        pl.col("bonus_cost").sum(),pl.col("contribution_30d").sum(),
        pl.col("bet_count_30d").sum(),pl.col("reached_bet").sum().alias("active_players"),
        pl.col("retained_d7").mean().alias("d7_retention"),
        pl.col("retained_d30").mean().alias("d30_retention")
    ).with_columns(pl.when(pl.col("stakes_30d")>0).then(pl.col("wins_30d")/pl.col("stakes_30d")).otherwise(None).alias("rtp")).sort(by)
