"""Typed configuration for the simulation and analysis pipeline.

Kept as plain dataclasses (no external config-parsing dependency) so the
whole project runs with nothing more exotic than polars/numpy/scipy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class BonusConfig:
    """Parameters of the bonus offer being tested."""

    match_rate: float = 1.0          # 100% match
    match_cap: float = 50.0          # capped at $50


@dataclass(frozen=True)
class SegmentEffects:
    """Segment-level baseline conversion adjustments (absolute, in probability units).

    These exist so the simulated dataset has real heterogeneity to
    discover during segmentation analysis, instead of a flat uplift
    everywhere.
    """

    country_lift: dict = field(
        default_factory=lambda: {
            "IN": 0.00, "BR": 0.02, "PH": -0.01, "ZA": 0.01,
            "DE": -0.02, "CA": 0.03, "MX": 0.00, "NG": -0.01,
        }
    )
    device_lift: dict = field(
        default_factory=lambda: {"mobile": 0.01, "desktop": -0.01}
    )
    vertical_lift: dict = field(
        default_factory=lambda: {"casino": 0.00, "sportsbook": 0.015}
    )


@dataclass(frozen=True)
class SimulationConfig:
    """Top-level simulation parameters."""

    n_players: int = 3_000_000
    seed: int = 42
    start_date: date = date(2025, 1, 1)
    window_days: int = 90

    base_deposit_p: float = 0.35
    treatment_deposit_lift: float = 0.045

    base_deposit_mean: float = 45.0
    treatment_deposit_amount_lift: float = 7.0
    deposit_amount_sigma: float = 0.6

    base_bet_p: float = 0.87
    treatment_bet_lift: float = 0.01

    base_repeat_p: float = 0.28
    treatment_repeat_lift: float = 0.055
    repeat_amount_mean: float = 38.0
    repeat_amount_sigma: float = 0.5

    bonus: BonusConfig = field(default_factory=BonusConfig)
    segments: SegmentEffects = field(default_factory=SegmentEffects)

    countries: tuple = ("IN", "BR", "PH", "ZA", "DE", "CA", "MX", "NG")
    country_weights: tuple = (0.22, 0.18, 0.12, 0.10, 0.10, 0.08, 0.12, 0.08)

    devices: tuple = ("mobile", "desktop")
    device_weights: tuple = (0.72, 0.28)

    channels: tuple = ("organic", "paid_social", "affiliate", "paid_search", "referral")
    channel_weights: tuple = (0.22, 0.28, 0.25, 0.15, 0.10)

    verticals: tuple = ("casino", "sportsbook")
    vertical_weights: tuple = (0.62, 0.38)


DEFAULT_CONFIG = SimulationConfig()
