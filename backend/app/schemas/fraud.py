from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class FraudFlagCreate(BaseModel):
    receipt_id: int
    flag_type: str
    severity: str
    description: str | None = None
    details: dict | None = None
    confidence_score: Decimal | None = None


class FraudAnalysisResult(BaseModel):
    """Result from the fraud detection pipeline."""
    receipt_id: int
    fraud_score: int
    risk_level: str
    flags: list[FraudFlagCreate]
    analyzed_at: datetime
