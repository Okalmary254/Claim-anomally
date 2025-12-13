import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os
import joblib
from sklearn.preprocessing import StandardScaler
from ml_pipeline.models.autoencoder import Autoencoder

# Configuration
MODEL_PATH = "data/autoencoder.pth"
SCALER_PATH = "data/scaler.pkl"
INPUT_DIM = 2 # Using Cost and Doctor Frequency for this simple MVP

def generate_mock_data(n_samples=1000):
    """
    Generate normal claim data for training (learning 'normal' behavior).
    """
    # Normal claims: Cost around $100-$500, Freq around 5-20
    costs = np.random.normal(300, 100, n_samples)
    freqs = np.random.normal(10, 5, n_samples)
    
    data = np.stack([costs, freqs], axis=1)
    return data

def train_model():
    print("Generating mock training data...")
    data = generate_mock_data()
    
    # Normalize
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data)
    
    # Convert to Tensor
    tensor_data = torch.FloatTensor(data_scaled)
    
    # Initialize Model
    model = Autoencoder(INPUT_DIM)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    print("Training Autoencoder...")
    epochs = 50
    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(tensor_data)
        loss = criterion(outputs, tensor_data)
        loss.backward()
        optimizer.step()
        
        if (epoch+1) % 10 == 0:
            print(f"Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}")
            
    # Save Model and Scaler
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    torch.save(model.state_dict(), MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"Model saved to {MODEL_PATH}")
    print(f"Scaler saved to {SCALER_PATH}")

if __name__ == "__main__":
    train_model()
