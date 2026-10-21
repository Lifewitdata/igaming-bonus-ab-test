"""Legacy deposit-volume ratio only. Use gaming.experiment_readout for revenue ROI."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoiResult:
    total_bonus_cost: float
    treatment_total_volume: float
    expected_volume_at_control_rate: float
    incremental_volume: float
    roi: float

    def recommendation(self, significant_lift: bool) -> str:
        return "DO NOT ROLL OUT AS BLANKET OFFER based on deposit volume: this proxy is not revenue ROI."


def compute_roi(
    control_total_volume: float,
    control_signups: int,
    treatment_total_volume: float,
    treatment_signups: int,
    treatment_total_bonus_cost: float,
) -> RoiResult:
    """Compute bonus ROI vs an expected-volume-at-control-rate counterfactual.

    The counterfactual assumes the treatment group, absent the bonus,
    would have generated volume per signup at the same rate as control.
    This is a simplifying assumption appropriate for a randomized A/B
    test (the two groups are drawn from the same population), but would
    need a more careful causal model outside of a clean randomized test.
    """
    expected_volume = (control_total_volume / control_signups) * treatment_signups
    incremental_volume = treatment_total_volume - expected_volume
    roi = (
        float("nan")
        if treatment_total_bonus_cost == 0
        else incremental_volume / treatment_total_bonus_cost
    )
    return RoiResult(
        total_bonus_cost=treatment_total_bonus_cost,
        treatment_total_volume=treatment_total_volume,
        expected_volume_at_control_rate=expected_volume,
        incremental_volume=incremental_volume,
        roi=roi,
    )
