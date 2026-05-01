"""Shared fixtures for all tests."""
from datetime import date
from decimal import Decimal

import pytest

from app.models.fraud_flag import FraudFlag
from app.models.policy_rule import PolicyRule
from app.models.receipt import Receipt


@pytest.fixture
def make_receipt():
    """Factory for Receipt ORM instances without a DB session."""
    def _make(
        id=1,
        merchant="Starbucks",
        amount=Decimal("15.47"),
        transaction_date=date(2024, 1, 15),
        category=None,
        employee_id=None,
        image_hash=None,
        status="analyzed",
    ):
        r = Receipt()
        r.id = id
        r.merchant = merchant
        r.amount = amount
        r.transaction_date = transaction_date
        r.category = category
        r.employee_id = employee_id
        r.image_hash = image_hash
        r.status = status
        return r
    return _make


@pytest.fixture
def make_rule():
    """Factory for PolicyRule ORM instances."""
    def _make(rule_type, parameters, severity="medium", rule_name=None, id=1):
        rule = PolicyRule()
        rule.id = id
        rule.rule_name = rule_name or f"Test {rule_type} rule"
        rule.rule_type = rule_type
        rule.parameters = parameters
        rule.severity = severity
        rule.is_active = True
        return rule
    return _make


@pytest.fixture
def make_flag():
    """Factory for FraudFlag ORM instances."""
    def _make(flag_type="duplicate", severity="high", confidence=100.0, receipt_id=1):
        flag = FraudFlag()
        flag.flag_type = flag_type
        flag.severity = severity
        flag.confidence_score = Decimal(str(confidence))
        flag.receipt_id = receipt_id
        return flag
    return _make
