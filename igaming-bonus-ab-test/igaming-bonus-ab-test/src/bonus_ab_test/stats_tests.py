"""Pure statistical functions for A/B test analysis.

Kept dependency-light (numpy + scipy only) and side-effect free so they're
easy to unit test in isolation from the simulation/Polars pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass(frozen=True)
class ProportionTestResult:
    p_control: float
    p_treatment: float
    absolute_lift: float
    relative_lift: float
    z_stat: float
    p_value: float
    ci_low: float
    ci_high: float

    @property
    def significant(self) -> bool:
        return self.p_value < 0.05


@dataclass(frozen=True)
class MeanTestResult:
    mean_control: float
    mean_treatment: float
    difference: float
    t_stat: float
    p_value: float

    @property
    def significant(self) -> bool:
        return self.p_value < 0.05


def two_proportion_ztest(x1: int, n1: int, x2: int, n2: int) -> ProportionTestResult:
    """Two-proportion z-test comparing a control (1) and treatment (2) group.

    Uses a pooled proportion for the z-statistic (standard for a
    difference-in-proportions significance test) and an unpooled
    standard error for the confidence interval on the lift, which is
    the more conservative / standard convention.

    Raises
    ------
    ValueError
        If either group has zero observations.
    """
    if n1 <= 0 or n2 <= 0:
        raise ValueError("Both groups must have at least one observation.")

    p1, p2 = x1 / n1, x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    se_pooled = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    z = 0.0 if se_pooled == 0 else (p2 - p1) / se_pooled
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))

    se_ci = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    diff = p2 - p1
    ci = (diff - 1.96 * se_ci, diff + 1.96 * se_ci)

    relative_lift = float("nan") if p1 == 0 else diff / p1

    return ProportionTestResult(
        p_control=p1,
        p_treatment=p2,
        absolute_lift=diff,
        relative_lift=relative_lift,
        z_stat=float(z),
        p_value=float(p_value),
        ci_low=float(ci[0]),
        ci_high=float(ci[1]),
    )


def welch_ttest(treatment: np.ndarray, control: np.ndarray) -> MeanTestResult:
    """Welch's t-test (unequal variance) comparing treatment vs control means."""
    t_stat, p_value = stats.ttest_ind(treatment, control, equal_var=False)
    return MeanTestResult(
        mean_control=float(np.mean(control)),
        mean_treatment=float(np.mean(treatment)),
        difference=float(np.mean(treatment) - np.mean(control)),
        t_stat=float(t_stat),
        p_value=float(p_value),
    )


def required_sample_size(
    baseline_rate: float,
    min_detectable_effect: float,
    alpha: float = 0.05,
    power: float = 0.8,
) -> int:
    """Minimum per-group sample size for a two-proportion z-test.

    Standard closed-form approximation for the sample size needed to
    detect an absolute `min_detectable_effect` lift over a
    `baseline_rate`, at the given significance level and power.
    """
    p1 = baseline_rate
    p2 = baseline_rate + min_detectable_effect
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)

    p_bar = (p1 + p2) / 2
    numerator = (
        z_alpha * np.sqrt(2 * p_bar * (1 - p_bar)) + z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    ) ** 2
    denominator = (p2 - p1) ** 2
    return int(np.ceil(numerator / denominator))
