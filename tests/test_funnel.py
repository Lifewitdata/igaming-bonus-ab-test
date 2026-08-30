import polars as pl
import pytest

from bonus_ab_test.funnel import funnel_by_group, segment_lift


@pytest.fixture
def sample_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "group": ["control", "control", "control", "treatment", "treatment", "treatment", "treatment"],
            "country": ["IN", "IN", "BR", "IN", "IN", "BR", "BR"],
            "reached_deposit": [True, False, True, True, True, True, False],
            "first_deposit_amount": [40.0, 0.0, 60.0, 50.0, 55.0, 45.0, 0.0],
            "reached_bet": [True, False, True, True, True, False, False],
            "repeat_deposit_30d": [True, False, False, True, True, False, False],
            "bonus_cost": [0.0, 0.0, 0.0, 40.0, 50.0, 45.0, 0.0],
            "ltv_30d": [70.0, 0.0, 60.0, 90.0, 100.0, 45.0, 0.0],
        }
    )


def test_funnel_by_group_row_counts(sample_df):
    funnel = funnel_by_group(sample_df)
    assert funnel.height == 2
    ctrl = funnel.filter(pl.col("group") == "control").row(0, named=True)
    trt = funnel.filter(pl.col("group") == "treatment").row(0, named=True)
    assert ctrl["signups"] == 3
    assert ctrl["deposits"] == 2
    assert trt["signups"] == 4
    assert trt["deposits"] == 3


def test_funnel_by_group_rates(sample_df):
    funnel = funnel_by_group(sample_df)
    ctrl = funnel.filter(pl.col("group") == "control").row(0, named=True)
    assert ctrl["signup_to_deposit_rate"] == pytest.approx(2 / 3)


def test_segment_lift_pivots_correctly(sample_df):
    seg = segment_lift(sample_df, "country")
    assert set(seg.columns) >= {"country", "control", "treatment", "lift_pp"}
    assert seg.height == 2  # IN and BR
