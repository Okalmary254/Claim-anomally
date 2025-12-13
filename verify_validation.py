import requests
import os

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "secret-token"
HEADERS = {"x-api-key": API_KEY}

# We need a file to upload. We'll create dummy text files.
# But specific content triggers specific regexes.
# 1. Incomplete Claim
INCOMPLETE_TEXT = "This is a random text with no claim info."
with open("test_incomplete.txt", "w") as f:
    f.write(INCOMPLETE_TEXT)

# 2. Complete Claim
COMPLETE_TEXT = """
Name of Doctor: Dr. House
Final Diagnosis: Lupus
Total Claims: $500.00
"""
with open("test_complete.txt", "w") as f:
    f.write(COMPLETE_TEXT)

def test_upload(filename, label):
    try:
        if filename != "Existing Image":
            # Test text file upload, API expects file
             with open(filename, "rb") as f:
                # We upload as PDF to trigger PDF extraction path (which might fail on text file, but let's see)
                # Or as jpg?
                # "test_incomplete.txt" -> we should rename it or just send it.
                # The API checks extension.
                 resp = requests.post(f"{BASE_URL}/predict", files={"file": (filename + ".pdf", f, "application/pdf")}, headers=HEADERS)
             
             print(f"Status: {resp.status_code}")
             if resp.status_code == 200:
                data = resp.json()
                print("Response Status:", data.get("status"))
                print("Issues:", data.get("issues"))
                print("Entities:", data.get("entities"))
             else:
                print("Error:", resp.text)
        
        else:
             # Existing Image test
             VALID_IMAGE = r"C:\Users\Hp\.gemini\antigravity\brain\d263254f-efcb-43e5-ba47-f39a2413a736\uploaded_image_0_1765574010812.png"
             if os.path.exists(VALID_IMAGE):
                with open(VALID_IMAGE, "rb") as f:
                     resp = requests.post(f"{BASE_URL}/predict", files={"file": ("claim.png", f, "image/png")}, headers=HEADERS)
                
                print(f"Status: {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    print("Response Status:", data.get("status"))
                    print("Issues:", data.get("issues"))
                    print("Entities:", data.get("entities"))
                else:
                    print("Error:", resp.text)
             else:
                print("Valid image not found.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_upload("test_incomplete.txt", "Incomplete Claim")
    test_upload("Existing Image", "Existing Image")
