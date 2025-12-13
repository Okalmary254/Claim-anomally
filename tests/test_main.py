from fastapi.testclient import TestClient
from backend.app.main import app
import os
import pytest
from unittest.mock import patch


# Valid API Key headers
VALID_HEADERS = {"x-api-key": "secret-token"}

client = TestClient(app)

# Mock the OCR function to avoid needing Tesseract installed in the test env
def mock_extract_text(file_path):
    return "Dr. Smith Diagnosis: Flu Cost: $100.00"

@patch("backend.app.api.extract_text_from_file", side_effect=mock_extract_text)
def test_predict_endpoint(mock_ocr):
    # Create a dummy file
    files = {'file': ('test.pdf', b'dummy content', 'application/pdf')}
    
    response = client.post("/predict", files=files, headers=VALID_HEADERS)
    
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "prediction" in data
    assert data["entities"]["doctor"] == "Smith"
    assert data["entities"]["cost"] == 100.0

def test_stats_endpoint():
    response = client.get("/stats", headers=VALID_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "total_claims" in data
    assert "high_risk_claims" in data

def test_feedback_endpoint():
    # Submit feedback for a dummy claim ID 1
    response = client.post("/feedback", json={"claim_id": 1, "is_fraud": True}, headers=VALID_HEADERS)
    assert response.status_code == 200
    assert "recorded" in response.json()["message"]

def test_unauthorized_access():
    # Try to access statistics without an API key
    response = client.get("/stats")
    assert response.status_code == 403
    assert response.json() == {"detail": "Could not validate credentials"}

    # Try with invalid key
    response = client.get("/stats", headers={"x-api-key": "wrong-token"})
    assert response.status_code == 403
