# Claim Fraud Detection System

An AI-powered system to detect anomalies and potential fraud in medical claim forms.

## Components
1.  **ML Pipeline**: Extracts text from PDFs/Images and computes risk features.
2.  **Backend API**: FastAPI service that manages the database and serves predictions.
3.  **Dashboard**: Streamlit UI for investigators to review claims and analytics.

## Setup & Installation

### Prerequisites
- Python 3.11+
- Tesseract OCR installed and added to PATH.

### 1. Install Dependencies
**Option A: Using pip (Recommended if Poetry is missing)**
```bash
pip install fastapi uvicorn streamlit pandas numpy scikit-learn pymupdf pytesseract python-multipart shap requests torch joblib
```

**Option B: Using Poetry**
```bash
poetry install
```

### 2. Run the Backend
Start the FastAPI server:
```bash
uvicorn backend.app.main:app --reload
```
The API will be available at `http://localhost:8000`.

### 3. Run the Dashboard
In a new terminal, start the Streamlit app:
```bash
streamlit run dashboard/app.py
```
The dashboard will open in your browser at `http://localhost:8501`.

## Usage
1.  Go to the **Submit Claim** page in the dashboard.
2.  Upload a claim form (PDF or Image).
3.  Click **Analyze Claim** to see extracted details and risk score.
4.  Provide feedback if the claim is valid or fraudulent to update the database.
5.  Check the **Dashboard Analytics** page for system-wide stats.
