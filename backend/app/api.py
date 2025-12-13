from fastapi import APIRouter, UploadFile, File, HTTPException, Security, status, Depends
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
import os
import shutil
import pandas as pd
from ml_pipeline.ingestion import extract_text_from_file
from ml_pipeline.features import preprocess_claim
from ml_pipeline.predict import detector
from .schemas import ClaimPredictionResponse, FeedbackRequest, FeedbackResponse, ClaimStats
import tempfile
import sqlite3
from datetime import datetime


# Security
API_KEY_NAME = "x-api-key"
API_KEY = "secret-token" # In production, this should be in os.environ
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(key: str = Security(api_key_header)):
    if key == API_KEY:
        return key
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials",
    )

router = APIRouter(dependencies=[Depends(get_api_key)])

# Database setup
DATABASE_PATH = "data/claims.db"

def init_db():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor TEXT,
            diagnosis TEXT,
            cost REAL,
            risk_score REAL,
            prediction TEXT,
            is_fraud INTEGER DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_historical_data():
    if not os.path.exists(DATABASE_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        df = pd.read_sql_query("SELECT doctor, diagnosis, cost FROM claims", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def save_claim(entities, risk_score, prediction):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO claims (doctor, diagnosis, cost, risk_score, prediction)
        VALUES (?, ?, ?, ?, ?)
    ''', (entities.get('doctor'), entities.get('diagnosis'), entities.get('cost'), risk_score, prediction))
    claim_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return claim_id

@router.on_event("startup")
async def startup_event():
    init_db()

@router.post("/predict", response_model=ClaimPredictionResponse)
async def predict_fraud(file: UploadFile = File(...)):
    """
    Endpoint to upload a claim file and get fraud prediction.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Save uploaded file temporarily
    # Save uploaded file temporarily using streaming to prevent DoS
    try:
        suffix = os.path.splitext(file.filename)[1]
        # Basic extension validation
        if suffix.lower() not in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
             raise HTTPException(status_code=400, detail="Unsupported file format")

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            # Stream the file content to disk
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error handling file upload")

    try:
        # Extract text
        try:
            text = extract_text_from_file(temp_path)
        except Exception as  ocr_error:
            print(f"OCR Failed: {ocr_error}")
            text = "" # Fallback to empty text
            
        if not text:
             # If text is empty (either OCR failed or file empty)
             entities = {}
             features = {}
             validation_issues = ["Unable to extract text - low quality or empty file"]
             
             return ClaimPredictionResponse(
                entities=entities,
                features=None,
                risk_score=None,
                prediction=None,
                status="Low Quality",
                issues=validation_issues
            )

        # Get historical data
        historical_data = get_historical_data()

        # Preprocess and get features
        entities, features = preprocess_claim(text, historical_data if not historical_data.empty else None)

        # Pre-Risk Validation Layer
        validation_issues = []
        if not entities.get('doctor'):
            validation_issues.append("Missing Doctor Name")
        if not entities.get('diagnosis'):
            validation_issues.append("Missing Diagnosis")
        if entities.get('cost') is None:
            validation_issues.append("Missing Cost")
            
        # Determine Status
        if validation_issues:
            status_summary = "Incomplete"
            risk_score = None
            prediction = None
            # We might still want to return features if possible, or just None
        else:
            status_summary = "Complete"
            
            # Advanced Risk Analysis using Autoencoder
            # The detector returns a reconstruction error (MSE Loss). 
            # We normalize this for display (assuming loss > 1.0 is very high anomaly)
            raw_anomaly_score = detector.predict(features)
            
            # If model is not loaded (returns 0 cost/fallback), use heuristic
            if raw_anomaly_score == 0 and 'cost_outlier_score' in features:
                 # Heuristic fallback
                 risk_score = min(1.0, max(0.0, (features.get('cost_outlier_score', 0) + 1) / 2))
            else:
                 # Normalize MSE loss to 0-1 range (Experimental saturation at 2.0 MSE)
                 risk_score = min(1.0, raw_anomaly_score / 2.0)
    
            prediction = "High Risk" if risk_score > 0.5 else "Low Risk"
    
            # Save to database
            save_claim(entities, risk_score, prediction)

        return ClaimPredictionResponse(
            entities=entities,
            features=features if status_summary == "Complete" else None,
            risk_score=risk_score,
            prediction=prediction,
            status=status_summary,
            issues=validation_issues
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Log the error internally (print for now), but return generic error to user
        print(f"Internal Error in predict: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

@router.get("/stats", response_model=ClaimStats)
async def get_claim_stats():
    """
    Endpoint to get statistics about processed claims.
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Get total claims
        cursor.execute("SELECT COUNT(*) FROM claims")
        result = cursor.fetchone()
        total_claims = result[0] if result else 0

        # Get risk distribution
        cursor.execute("SELECT COUNT(*) FROM claims WHERE risk_score > 0.6")
        result = cursor.fetchone()
        high_risk_claims = result[0] if result else 0

        cursor.execute("SELECT COUNT(*) FROM claims WHERE risk_score <= 0.6")
        result = cursor.fetchone()
        low_risk_claims = result[0] if result else 0

        # Get average risk score
        cursor.execute("SELECT AVG(risk_score) FROM claims")
        result = cursor.fetchone()
        average_risk_score = result[0] if result and result[0] is not None else 0.0

        # Get top doctors
        cursor.execute("SELECT doctor, COUNT(*) as count FROM claims WHERE doctor IS NOT NULL GROUP BY doctor ORDER BY count DESC LIMIT 5")
        top_doctors = {row[0]: row[1] for row in cursor.fetchall()}

        # Get top diagnoses
        cursor.execute("SELECT diagnosis, COUNT(*) as count FROM claims WHERE diagnosis IS NOT NULL GROUP BY diagnosis ORDER BY count DESC LIMIT 5")
        top_diagnoses = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        return ClaimStats(
            total_claims=total_claims,
            high_risk_claims=high_risk_claims,
            low_risk_claims=low_risk_claims,
            average_risk_score=average_risk_score,
            top_doctors=top_doctors,
            top_diagnoses=top_diagnoses
        )

    except Exception as e:
        print(f"Internal Error in stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackRequest):
    """
    Endpoint to submit feedback on a claim.
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE claims SET is_fraud = ? WHERE id = ?
        ''', (1 if feedback.is_fraud else 0, feedback.claim_id))
        conn.commit()
        conn.close()

        return FeedbackResponse(message=f"Feedback for claim {feedback.claim_id} recorded: {'Fraud' if feedback.is_fraud else 'Valid'}")
    except Exception as e:
        print(f"Internal Error in feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")