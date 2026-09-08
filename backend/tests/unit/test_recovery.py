"""Unit tests for the recovery score formula (section 14.1)."""

import pytest

from app.rules.recovery import compute_recovery_score


def test_all_maximum_scores_give_ten():
    assert compute_recovery_score(10, 10, 10, 1, None) == pytest.approx(10.0)


def test_all_minimum_scores_give_one():
    assert compute_recovery_score(1, 1, 1, 10, 10) == pytest.approx(1.0)


def test_weighted_example():
    # 0.3*5 + 0.25*8 + 0.15*6 + 0.2*(11-2) + 0.1*10 = 1.5+2+0.9+1.8+1.0 = 7.2
    assert compute_recovery_score(5, 8, 6, 2, None) == pytest.approx(7.2, abs=1e-6)


def test_null_pain_uses_full_credit():
    with_pain = compute_recovery_score(6, 7, 8, 4, 5)
    without_pain = compute_recovery_score(6, 7, 8, 4, None)
    assert without_pain > with_pain


def test_stress_inverts():
    assert compute_recovery_score(6, 7, 8, 2, None) > compute_recovery_score(6, 7, 8, 8, None)


def test_result_rounded_to_one_decimal():
    score = compute_recovery_score(6, 7, 8, 4, None)
    assert round(score, 1) == score
