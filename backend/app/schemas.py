from pydantic import BaseModel
from typing import Optional, Dict, Any

class ClaimPredictionResponse(BaseModel):
    entities: Dict[str, Any]
    features: Optional[Dict[str, Any]] = None
    risk_score: Optional[float] = None
    prediction: Optional[str] = None
    status: str # "Complete", "Incomplete", "Low Quality"
    issues: list[str] = []

class FeedbackRequest(BaseModel):
    claim_id: int
    is_fraud: bool

class FeedbackResponse(BaseModel):
    message: str

class ClaimStats(BaseModel):
    total_claims: int
    high_risk_claims: int
    low_risk_claims: int
    average_risk_score: float
    top_doctors: Dict[str, int]
    top_diagnoses: Dict[str, int]
