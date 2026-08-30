"""Simulates a large player-level A/B test dataset for a deposit-bonus offer.

Fully vectorized with numpy so it scales to millions of rows in seconds,
then assembled into a Polars DataFrame.
"""

from __future__ import annotations

import logging

import numpy as np
import polars as pl

from bonus_ab_test.config import DEFAULT_CONFIG, SimulationConfig

logger = logging.getLogger(__name__)


def simulate_players(cfg: SimulationConfig = DEFAULT_CONFIG) -> pl.DataFrame:
    """Generate a simulated player-level A/B test dataset.

    Parameters
    ----------
    cfg:
        Simulation configuration. Defaults to `DEFAULT_CONFIG`.

    Returns
    -------
    pl.DataFrame
        One row per player with funnel outcomes, deposit/bonus economics,
        and dimension columns for segmentation.
    """
    rng = np.random.default_rng(cfg.seed)
    n = cfg.n_players
    logger.info("Simulating %s players (seed=%s)", f"{n:,}", cfg.seed)

    player_id = np.arange(1, n + 1)
    signup_offset = rng.integers(0, cfg.window_days, size=n)

    country = rng.choice(np.array(cfg.countries), size=n, p=np.array(cfg.country_weights))
    device = rng.choice(np.array(cfg.devices), size=n, p=np.array(cfg.device_weights))
    channel = rng.choice(np.array(cfg.channels), size=n, p=np.array(cfg.channel_weights))
    vertical = rng.choice(np.array(cfg.verticals), size=n, p=np.array(cfg.vertical_weights))

    group = rng.choice(np.array(["control", "treatment"]), size=n, p=[0.5, 0.5])
    is_treatment = group == "treatment"

    seg = cfg.segments
    seg_adj = (
        np.vectorize(seg.country_lift.get)(country)
        + np.vectorize(seg.device_lift.get)(device)
        + np.vectorize(seg.vertical_lift.get)(vertical)
    )

    # --- Stage 1: signup -> first deposit ---------------------------------
    deposit_p = cfg.base_deposit_p + seg_adj + is_treatment * cfg.treatment_deposit_lift
    deposit_p = np.clip(deposit_p, 0.02, 0.95)
    reached_deposit = rng.random(n) < deposit_p

    mu = (
        np.log(cfg.base_deposit_mean + is_treatment * cfg.treatment_deposit_amount_lift)
        - 0.5 * cfg.deposit_amount_sigma ** 2
    )
    first_deposit_amount = np.where(
        reached_deposit,
        np.round(rng.lognormal(mean=mu, sigma=cfg.deposit_amount_sigma), 2),
        0.0,
    )

    # --- Stage 2: first deposit -> first bet -------------------------------
    bet_p = np.where(reached_deposit, cfg.base_bet_p + is_treatment * cfg.treatment_bet_lift, 0.0)
    reached_bet = (rng.random(n) < bet_p) & reached_deposit

    # --- Stage 3: repeat deposit within 30 days ----------------------------
    repeat_p = np.where(
        reached_deposit,
        np.clip(cfg.base_repeat_p + seg_adj + is_treatment * cfg.treatment_repeat_lift, 0.02, 0.9),
        0.0,
    )
    repeat_deposit_30d = (rng.random(n) < repeat_p) & reached_deposit

    repeat_deposit_amount = np.where(
        repeat_deposit_30d,
        np.round(
            rng.lognormal(
                mean=np.log(cfg.repeat_amount_mean) - 0.5 * cfg.repeat_amount_sigma ** 2,
                sigma=cfg.repeat_amount_sigma,
            ),
            2,
        ),
        0.0,
    )

    # --- Bonus cost ---------------------------------------------------------
    bonus_cost = np.where(
        is_treatment & reached_deposit,
        np.minimum(first_deposit_amount * cfg.bonus.match_rate, cfg.bonus.match_cap),
        0.0,
    )

    ltv_30d = first_deposit_amount + repeat_deposit_amount

    df = pl.DataFrame(
        {
            "player_id": player_id,
            "signup_offset": signup_offset,
            "country": country,
            "device": device,
            "channel": channel,
            "vertical": vertical,
            "group": group,
            "reached_deposit": reached_deposit,
            "first_deposit_amount": first_deposit_amount,
            "reached_bet": reached_bet,
            "repeat_deposit_30d": repeat_deposit_30d,
            "repeat_deposit_amount": repeat_deposit_amount,
            "bonus_cost": bonus_cost,
            "ltv_30d": ltv_30d,
        }
    ).with_columns(
        (pl.lit(cfg.start_date) + pl.duration(days=pl.col("signup_offset"))).alias("signup_date")
    ).drop("signup_offset")

    logger.info("Simulation complete: %s rows x %s cols", f"{df.height:,}", df.width)
    return df
