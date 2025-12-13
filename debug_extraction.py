from ml_pipeline.ingestion import extract_text_from_file
from ml_pipeline.features import preprocess_claim
import os

IMAGE_PATH = r"C:\Users\Hp\.gemini\antigravity\brain\d263254f-efcb-43e5-ba47-f39a2413a736\uploaded_image_0_1765574010812.png"

print(f"Analyzing {IMAGE_PATH}...")

try:
    # 1. Extract Text
    text = extract_text_from_file(IMAGE_PATH)
    print("\n--- RAW TEXT START ---")
    print(text)
    print("--- RAW TEXT END ---\n")

    # 2. Preprocess
    entities, features = preprocess_claim(text)
    print("Entities:", entities)
    print("Features:", features)

except Exception as e:
    print("ERROR OCCURRED:")
    print(str(e))
    # import traceback
    # traceback.print_exc()
