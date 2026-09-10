"""Unit tests for the sync rule-checker functions in policy_validator.

Tests import the private _check_* functions directly so each rule can be
exercised in isolation without a database or the full validate_receipt pipeline.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.models.fraud_flag import FraudFlag
from app.services.policy_validator import (
    _check_amount_limit,
    _check_future_date,
    _check_round_number,
    _check_vendor_category,
)


# ---------------------------------------------------------------------------
# amount_limit
# ---------------------------------------------------------------------------

class TestAmountLimit:
    def test_no_amount_skips(self, make_receipt, make_rule):
        receipt = make_receipt(amount=None)
        rule = make_rule("amount_limit", {"limit": 75.00})
        assert _check_amount_limit(rule, receipt) is None

    def test_missing_limit_param_skips(self, make_receipt, make_rule):
        receipt = make_receipt(amount=Decimal("80.00"))
        rule = make_rule("amount_limit", {})  # no "limit" key
        assert _check_amount_limit(rule, receipt) is None

    def test_under_limit_passes(self, make_receipt, make_rule):
        receipt = make_receipt(amount=Decimal("50.00"))
        rule = make_rule("amount_limit", {"limit": 75.00})
        assert _check_amount_limit(rule, receipt) is None

    def test_at_limit_passes(self, make_receipt, make_rule):
        """Exactly at the limit is not a violation (strictly greater than)."""
        receipt = make_receipt(amount=Decimal("75.00"))
        rule = make_rule("amount_limit", {"limit": 75.00})
        assert _check_amount_limit(rule, receipt) is None

    def test_over_limit_flags(self, make_receipt, make_rule):
        receipt = make_receipt(amount=Decimal("80.00"))
        rule = make_rule("amount_limit", {"limit": 75.00}, severity="medium")
        flag = _check_amount_limit(rule, receipt)
        assert isinstance(flag, FraudFlag)
        assert flag.flag_type == "policy_violation"
        assert flag.severity == "medium"
        assert flag.details["actual_amount"] == 80.0
        assert flag.details["limit"] == 75.0

    def test_category_filter_matches(self, make_receipt, make_rule):
        """Rule with category='meals' should fire when receipt category matches."""
        receipt = make_receipt(amount=Decimal("80.00"), category="meals")
        rule = make_rule("amount_limit", {"category": "meals", "limit": 75.00})
        assert _check_amount_limit(rule, receipt) is not None

    def test_category_filter_skips_wrong_category(self, make_receipt, make_rule):
        """Rule with category='meals' should NOT fire for a 'travel' receipt."""
        receipt = make_receipt(amount=Decimal("80.00"), category="travel")
        rule = make_rule("amount_limit", {"category": "meals", "limit": 75.00})
        assert _check_amount_limit(rule, receipt) is None

    def test_no_category_applies_to_all(self, make_receipt, make_rule):
        """A rule with no category should apply regardless of receipt category."""
        receipt = make_receipt(amount=Decimal("300.00"), category="supplies")
        rule = make_rule("amount_limit", {"limit": 200.00})
        assert _check_amount_limit(rule, receipt) is not None

    def test_category_comparison_is_case_insensitive(self, make_receipt, make_rule):
        receipt = make_receipt(amount=Decimal("80.00"), category="MEALS")
        rule = make_rule("amount_limit", {"category": "meals", "limit": 75.00})
        assert _check_amount_limit(rule, receipt) is not None


# ---------------------------------------------------------------------------
# future_date
# ---------------------------------------------------------------------------

class TestFutureDate:
    def test_no_date_skips(self, make_receipt, make_rule):
        receipt = make_receipt(transaction_date=None)
        rule = make_rule("future_date", {}, severity="high")
        assert _check_future_date(rule, receipt) is None

    def test_past_date_passes(self, make_receipt, make_rule):
        receipt = make_receipt(transaction_date=date(2020, 1, 1))
        rule = make_rule("future_date", {})
        assert _check_future_date(rule, receipt) is None

    def test_today_passes(self, make_receipt, make_rule):
        receipt = make_receipt(transaction_date=date.today())
        rule = make_rule("future_date", {})
        assert _check_future_date(rule, receipt) is None

    def test_tomorrow_flags(self, make_receipt, make_rule):
        receipt = make_receipt(transaction_date=date.today() + timedelta(days=1))
        rule = make_rule("future_date", {}, severity="high")
        flag = _check_future_date(rule, receipt)
        assert isinstance(flag, FraudFlag)
        assert flag.flag_type == "policy_violation"
        assert flag.severity == "high"
        assert flag.confidence_score == Decimal("100.00")

    def test_far_future_flags(self, make_receipt, make_rule):
        receipt = make_receipt(transaction_date=date(2099, 12, 31))
        rule = make_rule("future_date", {})
        assert _check_future_date(rule, receipt) is not None


# ---------------------------------------------------------------------------
# vendor_category
# ---------------------------------------------------------------------------

_ALLOWED_CATEGORIES = {
    "allowed_categories": {
        "meals":    ["restaurant", "cafe", "starbucks", "coffee", "food"],
        "travel":   ["hotel", "delta", "marriott", "uber"],
        "supplies": ["staples", "amazon", "office depot", "target"],
    }
}


class TestVendorCategory:
    def test_no_merchant_skips(self, make_receipt, make_rule):
        receipt = make_receipt(merchant=None)
        rule = make_rule("vendor_category", _ALLOWED_CATEGORIES)
        assert _check_vendor_category(rule, receipt) is None

    def test_empty_allowed_categories_skips(self, make_receipt, make_rule):
        receipt = make_receipt(merchant="Starbucks")
        rule = make_rule("vendor_category", {"allowed_categories": {}})
        assert _check_vendor_category(rule, receipt) is None

    def test_known_merchant_passes(self, make_receipt, make_rule):
        receipt = make_receipt(merchant="Starbucks")
        rule = make_rule("vendor_category", _ALLOWED_CATEGORIES)
        assert _check_vendor_category(rule, receipt) is None

    def test_case_insensitive_match_passes(self, make_receipt, make_rule):
        receipt = make_receipt(merchant="STARBUCKS RESERVE #1234")
        rule = make_rule("vendor_category", _ALLOWED_CATEGORIES)
        assert _check_vendor_category(rule, receipt) is None

    def test_partial_name_match_passes(self, make_receipt, make_rule):
        """'Marriott Downtown' should match via 'marriott' keyword."""
        receipt = make_receipt(merchant="Marriott Downtown Chicago")
        rule = make_rule("vendor_category", _ALLOWED_CATEGORIES)
        assert _check_vendor_category(rule, receipt) is None

    def test_unknown_merchant_flags(self, make_receipt, make_rule):
        receipt = make_receipt(merchant="Rainbow Roll Sushi")
        rule = make_rule("vendor_category", _ALLOWED_CATEGORIES, severity="medium")
        flag = _check_vendor_category(rule, receipt)
        assert isinstance(flag, FraudFlag)
        assert flag.flag_type == "policy_violation"
        assert flag.severity == "medium"
        assert flag.confidence_score == Decimal("85.00")
        assert flag.details["merchant"] == "Rainbow Roll Sushi"

    def test_target_matches_supplies(self, make_receipt, make_rule):
        """'TARGET' should match 'target' keyword in supplies category."""
        receipt = make_receipt(merchant="TARGET")
        rule = make_rule("vendor_category", _ALLOWED_CATEGORIES)
        assert _check_vendor_category(rule, receipt) is None


# ---------------------------------------------------------------------------
# round_number
# ---------------------------------------------------------------------------

class TestRoundNumber:
    def test_no_amount_skips(self, make_receipt, make_rule):
        receipt = make_receipt(amount=None)
        rule = make_rule("round_number", {"min_amount": 10.00})
        assert _check_round_number(rule, receipt) is None

    def test_below_threshold_skips(self, make_receipt, make_rule):
        """$5.00 is round but below the $10 minimum — should not flag."""
        receipt = make_receipt(amount=Decimal("5.00"))
        rule = make_rule("round_number", {"min_amount": 10.00})
        assert _check_round_number(rule, receipt) is None

    def test_normal_cents_passes(self, make_receipt, make_rule):
        receipt = make_receipt(amount=Decimal("48.75"))
        rule = make_rule("round_number", {"min_amount": 10.00})
        assert _check_round_number(rule, receipt) is None

    def test_non_round_odd_cents_passes(self, make_receipt, make_rule):
        receipt = make_receipt(amount=Decimal("65.77"))
        rule = make_rule("round_number", {"min_amount": 10.00})
        assert _check_round_number(rule, receipt) is None

    def test_zero_cents_flags(self, make_receipt, make_rule):
        receipt = make_receipt(amount=Decimal("50.00"))
        rule = make_rule("round_number", {"min_amount": 10.00}, severity="low")
        flag = _check_round_number(rule, receipt)
        assert isinstance(flag, FraudFlag)
        assert flag.flag_type == "policy_violation"
        assert flag.severity == "low"
        assert flag.confidence_score == Decimal("70.00")

    def test_fifty_cents_flags(self, make_receipt, make_rule):
        """$25.50 should be flagged as suspiciously round."""
        receipt = make_receipt(amount=Decimal("25.50"))
        rule = make_rule("round_number", {"min_amount": 10.00})
        assert _check_round_number(rule, receipt) is not None

    def test_exactly_at_threshold_flags(self, make_receipt, make_rule):
        """$10.00 is exactly at the min_amount threshold and should be flagged."""
        receipt = make_receipt(amount=Decimal("10.00"))
        rule = make_rule("round_number", {"min_amount": 10.00})
        assert _check_round_number(rule, receipt) is not None

    def test_large_round_amount_flags(self, make_receipt, make_rule):
        receipt = make_receipt(amount=Decimal("200.00"))
        rule = make_rule("round_number", {"min_amount": 10.00})
        assert _check_round_number(rule, receipt) is not None

    def test_default_min_amount_when_param_missing(self, make_receipt, make_rule):
        """Missing min_amount param should default to 10.00."""
        receipt = make_receipt(amount=Decimal("50.00"))
        rule = make_rule("round_number", {})  # no min_amount
        assert _check_round_number(rule, receipt) is not None
