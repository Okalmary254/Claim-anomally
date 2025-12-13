import re
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np

def clean_text(text):
    """
    Clean and normalize text: remove extra spaces, lowercase, etc.
    """
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def extract_entities(text):
    """
    Extract entities from text: Doctor, Diagnosis, Cost.
    Using simple regex patterns. In production, use NLP models.
    """
    entities = {}

    ent_str = text.replace('\n', ' ')
    
    # Extract Doctor
    # Matches: "Name of Doctor: ...", "Dr. ...", "Doctor: ..."
    doctor_patterns = [
        r'(?:name of )?doctor\s*[:\.]?\s*(?:dr[\.]?)?\s*([a-z\s]+)',
        r'dr\.?\s*([a-z\s]+)'
    ]
    for pattern in doctor_patterns:
        match = re.search(pattern, ent_str)
        if match:
            entities['doctor'] = match.group(1).strip()
            break
    if 'doctor' not in entities:
        entities['doctor'] = None

    # Extract Diagnosis
    # Matches: "Final Diagnosis...", "Diagnosis: ...", "Condition treated: ..."
    diagnosis_patterns = [
        r'(?:final )?diagnosis(?: of condition treated)?\s*[:\.]?\s*([a-z0-9\s\.]+)',
        r'diagnosis\s*[:\.]?\s*([a-z0-9\s]+)'
    ]
    for pattern in diagnosis_patterns:
        match = re.search(pattern, ent_str)
        if match:
            entities['diagnosis'] = match.group(1).strip()
            break
    if 'diagnosis' not in entities:
        entities['diagnosis'] = None

    # Extract Cost
    # Matches: "Total Claims...", "Cost: ...", "Fees: ..." or loose currency
    # Note: simple regex might match dates/phones. We try to be specific first.
    cost_patterns = [
        r'total claims\s*[\.:]?\s*[\$]?\s*(\d+\.?\d*)',
        r'cost\s*[:\.]?\s*[\$]?\s*(\d+\.?\d*)',
        r'fees\s*[:\.]?\s*[\$]?\s*(\d+\.?\d*)',
    ]
    for pattern in cost_patterns:
        match = re.search(pattern, ent_str)
        if match:
             try:
                entities['cost'] = float(match.group(1))
                break
             except:
                 pass
                 
    # Fallback to loose search if specific labels fail, but exclude dates/phones if possible
    if 'cost' not in entities:
        # Find all numbers that look like costs (e.g. 100.00, 500)
        # Avoid years (2025), phones (0800...). 
        # Heuristic: look for float format or number appearing near "$"
        loose_match = re.search(r'\$\s*(\d+\.?\d*)', ent_str)
        if loose_match:
             entities['cost'] = float(loose_match.group(1))
        else:
             entities['cost'] = None

    return entities

def compute_features(entities, historical_data=None):
    """
    Compute features: frequency, outliers, etc.
    If historical_data is provided, compute relative features.
    """
    features = {}

    # Basic features from entities
    features['cost'] = entities.get('cost', 0)

    # Frequency features (if historical data available)
    if historical_data is not None:
        # Frequency of doctor
        doctor_freq = historical_data['doctor'].value_counts().get(entities.get('doctor'), 0)
        features['doctor_frequency'] = doctor_freq

        # Frequency of diagnosis
        diagnosis_freq = historical_data['diagnosis'].value_counts().get(entities.get('diagnosis'), 0)
        features['diagnosis_frequency'] = diagnosis_freq

        # Outlier detection on cost
        costs = historical_data['cost'].dropna()
        if len(costs) > 0:
            scaler = StandardScaler()
            scaled_costs = scaler.fit_transform(costs.values.reshape(-1, 1))
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            iso_forest.fit(scaled_costs)
            scaled_cost = scaler.transform([[features['cost']]])
            features['cost_outlier_score'] = iso_forest.decision_function(scaled_cost)[0]
        else:
            features['cost_outlier_score'] = 0
    else:
        features['doctor_frequency'] = 0
        features['diagnosis_frequency'] = 0
        features['cost_outlier_score'] = 0

    return features

def preprocess_claim(text, historical_data=None):
    """
    Full preprocessing pipeline: clean, extract, compute features.
    """
    cleaned_text = clean_text(text)
    entities = extract_entities(cleaned_text)
    features = compute_features(entities, historical_data)
    return entities, features

if __name__ == "__main__":
    # Example usage
    sample_text = "Dr. John Doe Diagnosis: Broken leg Cost: $500"
    entities, features = preprocess_claim(sample_text)
    print("Entities:", entities)
    print("Features:", features)