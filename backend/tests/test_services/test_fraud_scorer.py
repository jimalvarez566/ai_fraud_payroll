"""Unit tests for fraud_scorer.calculate_score."""
from decimal import Decimal

import pytest

from app.services.fraud_scorer import calculate_score


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _flag(flag_type="duplicate", severity="high", confidence=100.0):
    """Minimal FraudFlag-like object (no DB needed)."""
    from app.models.fraud_flag import FraudFlag
    f = FraudFlag()
    f.flag_type = flag_type
    f.severity = severity
    f.confidence_score = Decimal(str(confidence))
    return f


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_no_flags_returns_zero_low():
    score, level = calculate_score([])
    assert score == 0
    assert level == "low"


def test_none_confidence_treated_as_100():
    """A flag with no confidence_score should default to 100%."""
    f = _flag()
    f.confidence_score = None
    score, level = calculate_score([f])
    assert score == 75   # duplicate high base = 75, full weight
    assert level == "high"


def test_unknown_type_uses_default_base():
    """Unrecognised (flag_type, severity) combos fall back to _DEFAULT_BASE_SCORE=20."""
    f = _flag(flag_type="future_alien_signal", severity="extreme")
    score, level = calculate_score([f])
    assert score == 20
    assert level == "low"


# ---------------------------------------------------------------------------
# Single-flag scores
# ---------------------------------------------------------------------------

def test_single_duplicate_high_100pct():
    score, level = calculate_score([_flag("duplicate", "high", 100)])
    assert score == 75
    assert level == "high"


def test_single_duplicate_medium_100pct():
    score, level = calculate_score([_flag("duplicate", "medium", 100)])
    assert score == 55
    assert level == "medium"


def test_single_duplicate_low_100pct():
    score, level = calculate_score([_flag("duplicate", "low", 100)])
    assert score == 35
    assert level == "medium"


def test_single_policy_high_100pct():
    score, level = calculate_score([_flag("policy_violation", "high", 100)])
    assert score == 50
    assert level == "medium"


def test_single_policy_medium_100pct():
    """Exactly at the medium threshold boundary."""
    score, level = calculate_score([_flag("policy_violation", "medium", 100)])
    assert score == 30
    assert level == "medium"


def test_single_policy_medium_85pct():
    """vendor_category flags use 85% confidence — should produce a low score."""
    score, level = calculate_score([_flag("policy_violation", "medium", 85)])
    # 30 * 0.85 = 25.5 → rounds to 26
    assert score == 26
    assert level == "low"


def test_single_policy_low_100pct():
    score, level = calculate_score([_flag("policy_violation", "low", 100)])
    assert score == 15
    assert level == "low"


# ---------------------------------------------------------------------------
# Confidence scaling
# ---------------------------------------------------------------------------

def test_confidence_scales_score():
    """Half confidence should produce roughly half the base score."""
    full = calculate_score([_flag("duplicate", "high", 100)])[0]
    half = calculate_score([_flag("duplicate", "high", 50)])[0]
    assert half == round(full * 0.5)


# ---------------------------------------------------------------------------
# Diminishing returns on multiple flags
# ---------------------------------------------------------------------------

def test_two_flags_second_contributes_half():
    """Second flag should add 50% of its individual score."""
    one = calculate_score([_flag("policy_violation", "medium", 100)])[0]   # 30
    two = calculate_score([
        _flag("policy_violation", "medium", 100),
        _flag("policy_violation", "medium", 100),
    ])[0]
    # 30 * 1.0 + 30 * 0.5 = 45
    assert two == 45


def test_three_flags_diminishing_returns():
    """Each successive flag contributes half the weight of the previous."""
    score, _ = calculate_score([
        _flag("policy_violation", "medium", 100),  # 30 * 1.00 = 30
        _flag("policy_violation", "medium", 100),  # 30 * 0.50 = 15
        _flag("policy_violation", "medium", 100),  # 30 * 0.25 =  7.5
    ])
    # total = 52.5 → round(52.5) = 52 (banker's rounding)
    assert score == 52


def test_flags_sorted_highest_first():
    """Higher-scoring flags should be weighted at 100%, lower ones at 50%."""
    # low flag first in list, high flag second — result should be same as reversed
    score_a, _ = calculate_score([
        _flag("policy_violation", "low",  100),   # base 15
        _flag("duplicate",        "high", 100),   # base 75
    ])
    score_b, _ = calculate_score([
        _flag("duplicate",        "high", 100),
        _flag("policy_violation", "low",  100),
    ])
    # Both should equal: 75 * 1.0 + 15 * 0.5 = 82 (rounded)
    assert score_a == score_b == round(75 * 1.0 + 15 * 0.5)


# ---------------------------------------------------------------------------
# Score capping
# ---------------------------------------------------------------------------

def test_score_capped_at_100():
    many_flags = [_flag("duplicate", "high", 100) for _ in range(10)]
    score, level = calculate_score(many_flags)
    assert score == 100
    assert level == "high"


# ---------------------------------------------------------------------------
# Risk level thresholds
# ---------------------------------------------------------------------------

def test_risk_level_boundary_low_to_medium():
    """29 → low, 30 → medium."""
    # policy_violation medium 100% → exactly 30 → medium
    _, level_30 = calculate_score([_flag("policy_violation", "medium", 100)])
    assert level_30 == "medium"

    # policy_violation medium 96% → 30 * 0.96 = 28.8 → 29 → low
    _, level_29 = calculate_score([_flag("policy_violation", "medium", 96)])
    assert level_29 == "low"


def test_risk_level_boundary_medium_to_high():
    """69 → medium, 70 → high."""
    # duplicate high at 92% → 75 * 0.92 = 69 → medium
    _, level_69 = calculate_score([_flag("duplicate", "high", 92)])
    assert level_69 == "medium"

    # duplicate high at 93.4% → 75 * 0.934 = 70.05 → 70 → high
    _, level_70 = calculate_score([_flag("duplicate", "high", 93.4)])
    assert level_70 == "high"
