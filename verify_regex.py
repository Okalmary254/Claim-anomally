from ml_pipeline.features import extract_entities
import traceback

SAMPLE_TEXT = """
TO BE FILLED BY DOCTOR
Final Diagnosis of condition treated: Z00.0 General Medical Exam
Name of Doctor : Dr. Omany
Telephone Number: 0800720...
Total Claims................
"""

try:
    print("Testing extraction on sample text...")
    
    # Mock clean_text behavior
    cleaned_text = SAMPLE_TEXT.lower().replace('\n', ' ').strip()
    print(f"Cleaned Text: {cleaned_text}")

    entities = extract_entities(cleaned_text)
    print("Extracted Entities:", entities)

    if entities.get('doctor') and ('omany' in entities['doctor']):
        print("PASS: Doctor extracted")
    else:
        print(f"FAIL: Doctor not extracted. Got: {entities.get('doctor')}")

    if entities.get('diagnosis') and ('z00.0' in entities['diagnosis'] or 'general' in entities['diagnosis']):
        print("PASS: Diagnosis extracted")
    else:
        print(f"FAIL: Diagnosis not extracted. Got: {entities.get('diagnosis')}")

except Exception as e:
    print("ERROR OCCURRED:")
    traceback.print_exc()
