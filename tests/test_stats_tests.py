import numpy as np
import pytest

from bonus_ab_test.stats_tests import (
    required_sample_size,
    two_proportion_ztest,
    welch_ttest,
)


def test_two_proportion_ztest_no_difference_not_significant():
    result = two_proportion_ztest(x1=500, n1=1000, x2=500, n2=1000)
    assert result.p_control == pytest.approx(0.5)
    assert result.p_treatment == pytest.approx(0.5)
    assert result.absolute_lift == pytest.approx(0.0)
    assert not result.significant


def test_two_proportion_ztest_large_difference_significant():
    # Large, clearly-different sample: control 30%, treatment 40%, n=10000 each
    result = two_proportion_ztest(x1=3000, n1=10000, x2=4000, n2=10000)
    assert result.p_control == pytest.approx(0.30)
    assert result.p_treatment == pytest.approx(0.40)
    assert result.absolute_lift == pytest.approx(0.10)
    assert result.significant
    assert result.p_value < 0.001
    # CI should not contain zero given the strong effect
    assert result.ci_low > 0


def test_two_proportion_ztest_relative_lift():
    result = two_proportion_ztest(x1=100, n1=1000, x2=110, n2=1000)
    assert result.relative_lift == pytest.approx(0.10, rel=1e-6)


def test_two_proportion_ztest_raises_on_empty_group():
    with pytest.raises(ValueError):
        two_proportion_ztest(x1=0, n1=0, x2=10, n2=100)


def test_welch_ttest_identical_distributions_not_significant():
    rng = np.random.default_rng(0)
    control = rng.normal(50, 10, size=5000)
    treatment = rng.normal(50, 10, size=5000)
    result = welch_ttest(treatment, control)
    assert not result.significant


def test_welch_ttest_clear_difference_significant():
    rng = np.random.default_rng(0)
    control = rng.normal(45, 10, size=5000)
    treatment = rng.normal(55, 10, size=5000)
    result = welch_ttest(treatment, control)
    assert result.significant
    assert result.difference == pytest.approx(10, abs=1.0)


def test_required_sample_size_reasonable_magnitude():
    # Detecting a 5pp lift over a 35% baseline should need on the order
    # of a few thousand per group, not ten or a few million.
    n = required_sample_size(baseline_rate=0.35, min_detectable_effect=0.05)
    assert 500 < n < 20000


def test_required_sample_size_smaller_effect_needs_more_samples():
    n_large_effect = required_sample_size(baseline_rate=0.35, min_detectable_effect=0.10)
    n_small_effect = required_sample_size(baseline_rate=0.35, min_detectable_effect=0.02)
    assert n_small_effect > n_large_effect
