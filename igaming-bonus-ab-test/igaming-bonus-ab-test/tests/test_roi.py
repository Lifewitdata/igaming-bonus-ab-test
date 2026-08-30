import pytest

from bonus_ab_test.roi import compute_roi


def test_compute_roi_positive_case():
    result = compute_roi(
        control_total_volume=100_000,
        control_signups=10_000,
        treatment_total_volume=150_000,
        treatment_signups=10_000,
        treatment_total_bonus_cost=20_000,
    )
    # expected volume at control rate == control_total_volume (equal signups)
    assert result.expected_volume_at_control_rate == pytest.approx(100_000)
    assert result.incremental_volume == pytest.approx(50_000)
    assert result.roi == pytest.approx(2.5)
    assert "ROLL OUT" in result.recommendation(significant_lift=True)
    assert "DO NOT" in result.recommendation(significant_lift=False)


def test_compute_roi_negative_case_below_one():
    result = compute_roi(
        control_total_volume=100_000,
        control_signups=10_000,
        treatment_total_volume=110_000,
        treatment_signups=10_000,
        treatment_total_bonus_cost=50_000,
    )
    assert result.roi < 1.0
    rec = result.recommendation(significant_lift=True)
    assert "DO NOT ROLL OUT AS BLANKET" in rec


def test_compute_roi_handles_zero_bonus_cost():
    result = compute_roi(
        control_total_volume=100_000,
        control_signups=10_000,
        treatment_total_volume=110_000,
        treatment_signups=10_000,
        treatment_total_bonus_cost=0,
    )
    import math
    assert math.isnan(result.roi)
