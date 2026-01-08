# api/index.py
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.main import app

app = FastAPI(title="Claim Fraud Detection API")

__all__ = ["app"]
# # Add CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.get("/")
# def read_root():
#     return {
#         "message": "Claim Fraud Detection API",
#         "status": "running",
#         "note": "ML inference endpoints disabled on serverless deployment"
#     }

# @app.get("/health")
# def health_check():
#     return {"status": "healthy"}
