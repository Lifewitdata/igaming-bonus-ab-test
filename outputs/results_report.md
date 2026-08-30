# Bonus A/B Test — Results Report

Dataset: 3,000,000 players

## 1. Funnel by Group

| group     |   signups |   deposits |   signup_to_deposit_rate |   deposit_to_bet_rate |   repeat_deposit_rate |   avg_first_deposit |
|:----------|----------:|-----------:|-------------------------:|----------------------:|----------------------:|--------------------:|
| control   |   1499012 |     544129 |                 0.362992 |              0.870545 |              0.293419 |             45.0052 |
| treatment |   1500988 |     612024 |                 0.407747 |              0.880461 |              0.348316 |             52.0389 |

## 2. Statistical Significance

**Signup → Deposit conversion**
- Control: 36.2992%  |  Treatment: 40.7747%
- Absolute lift: +4.4756% (relative: +12.33%)
- z = 79.64, p-value = 0.00e+00, 95% CI on lift: [4.3655%, 4.5856%]
- **Statistically significant at α = 0.05**

**Repeat-deposit rate within 30d (among depositors)**
- Control: 29.3419%  |  Treatment: 34.8316%
- Absolute lift: +5.4897% (relative: +18.71%)
- z = 63.03, p-value = 0.00e+00, 95% CI on lift: [5.3197%, 5.6597%]
- **Statistically significant at α = 0.05**

**First deposit amount (among depositors)**
- Control mean: $45.01  |  Treatment mean: $52.04
- Difference: $+7.03
- t = 118.51, p-value = 0.00e+00
- **Statistically significant at α = 0.05**

## 3. Bonus ROI

- Total bonus paid out (treatment group): **$23,851,495.03**
- Treatment group total 30-day deposit volume (LTV proxy): $37,052,751.38
- Expected volume at control's conversion/spend rate: $28,423,287.60
- **Estimated incremental 30-day deposit volume: $8,629,463.78**
- **ROI (incremental volume / bonus cost): 0.36x**

## 4. Segmentation: Signup → Deposit Lift by Segment

**By country:**
| country   |   treatment |   control |   lift_pp |
|:----------|------------:|----------:|----------:|
| CA        |      0.4357 |    0.3894 |    0.0463 |
| NG        |      0.3967 |    0.3510 |    0.0457 |
| IN        |      0.4048 |    0.3595 |    0.0452 |
| BR        |      0.4248 |    0.3797 |    0.0451 |
| ZA        |      0.4145 |    0.3699 |    0.0446 |
| PH        |      0.3941 |    0.3499 |    0.0442 |
| DE        |      0.3838 |    0.3397 |    0.0440 |
| MX        |      0.4042 |    0.3612 |    0.0430 |

**By device:**
| device   |   treatment |   control |   lift_pp |
|:---------|------------:|----------:|----------:|
| mobile   |      0.4136 |    0.3687 |    0.0449 |
| desktop  |      0.3927 |    0.3484 |    0.0444 |

**By vertical:**
| vertical   |   treatment |   control |   lift_pp |
|:-----------|------------:|----------:|----------:|
| casino     |      0.4027 |    0.3570 |    0.0457 |
| sportsbook |      0.4160 |    0.3727 |    0.0433 |

**By channel:**
| channel     |   treatment |   control |   lift_pp |
|:------------|------------:|----------:|----------:|
| paid_search |      0.4075 |    0.3613 |    0.0462 |
| referral    |      0.4075 |    0.3617 |    0.0458 |
| affiliate   |      0.4090 |    0.3635 |    0.0455 |
| paid_social |      0.4076 |    0.3633 |    0.0443 |
| organic     |      0.4067 |    0.3637 |    0.0430 |

## 5. Charts

Saved to `outputs/`: `funnel_comparison.png`, `conversion_rates.png`, `lift_by_country.png`

## 6. Recommendation

DO NOT ROLL OUT AS BLANKET OFFER: lift is significant but bonus cost exceeds incremental volume. Consider targeting only high-lift segments or lowering the match cap.