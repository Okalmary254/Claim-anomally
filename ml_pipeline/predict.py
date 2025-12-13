import torch
import joblib
import numpy as np
import os
from ml_pipeline.models.autoencoder import Autoencoder

MODEL_PATH = "data/autoencoder.pth"
SCALER_PATH = "data/scaler.pkl"
INPUT_DIM = 2

class AnomalyDetector:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.load_model()

    def load_model(self):
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
            self.model = Autoencoder(INPUT_DIM)
            self.model.load_state_dict(torch.load(MODEL_PATH))
            self.model.eval()
            self.scaler = joblib.load(SCALER_PATH)
        else:
            print("Model not found, using heuristics.")
    
    def predict(self, features):
        """
        Predict anomaly score. High score = Anomaly.
        features: dict with 'cost' and 'doctor_frequency'
        """
        if not self.model or not self.scaler:
            return 0.0 # Fallback
            
        # Prepare input
        # Assuming features are provided
        input_data = np.array([[features.get('cost', 0), features.get('doctor_frequency', 0)]])
        
        # Scale
        scaled_data = self.scaler.transform(input_data)
        tensor_data = torch.FloatTensor(scaled_data)
        
        # Reconstruct
        with torch.no_grad():
            reconstructed = self.model(tensor_data)
            
        # Compute MSE loss as anomaly score
        loss = torch.mean((tensor_data - reconstructed) ** 2).item()
        return loss

# Singleton instance
detector = AnomalyDetector()
