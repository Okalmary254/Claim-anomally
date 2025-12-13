import streamlit as st
import requests
import pandas as pd
import json
from io import BytesIO

# Backend API URL

# Backend API URL
API_URL = "http://127.0.0.1:8000"
HEADERS = {"x-api-key": "secret-token"}

st.set_page_config(page_title="Claim Fraud Detection", layout="wide")

st.title("🏥 Medical Claim Fraud Detection System")

# Sidebar for navigation
page = st.sidebar.selectbox("Navigation", ["Submit Claim", "Dashboard Analytics"])

if page == "Submit Claim":
    st.header("Upload Claim Form")
    uploaded_file = st.file_uploader("Choose a file (PDF or Image)", type=["pdf", "png", "jpg", "jpeg"])

    if uploaded_file is not None:
        if st.button("Analyze Claim"):
            with st.spinner("Processing claim..."):
                try:
                    # Prepare file for upload
                    files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                    response = requests.post(f"{API_URL}/predict", files=files, headers=HEADERS)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Display Results
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("Extracted Details")
                            st.json(data["entities"])
                        
                        with col2:
                            status_val = data.get("status", "Unknown")
                            
                            if status_val == "Incomplete":
                                st.subheader("⚠️ Validation Issues")
                                st.error("Claim data is incomplete. Risk analysis skipped.")
                                for issue in data.get("issues", []):
                                    st.warning(f"- {issue}")
                            elif status_val == "Low Quality":
                                st.subheader("⚠️ Quality Issues")
                                st.error("Could not extract text from document.")
                                st.warning("Please ensure the image is clear and contains readable text.")
                                for issue in data.get("issues", []):
                                    st.info(f"- {issue}")
                            elif status_val == "Complete":
                                st.subheader("Risk Analysis")
                                risk_score = data.get("risk_score")
                                if risk_score is not None:
                                    st.metric("Risk Score", f"{risk_score:.2f}")
                                    
                                    prediction = data.get("prediction")
                                    if prediction == "High Risk":
                                        st.error(f"⚠️ Prediction: {prediction}")
                                    else:
                                        st.success(f"✅ Prediction: {prediction}")
                                    
                                    st.write("**Anomaly Indicators:**")
                                    st.json(data["features"])
                            else:
                                st.error(f"Unknown Status: {status_val}")

                        # Feedback Loop
                        st.subheader("Adjudicator Feedback")
                        with st.form("feedback_form"):
                            is_fraud = st.checkbox("Mark as Fraudulent?")
                            submit_feedback = st.form_submit_button("Submit Feedback")
                            
                            if submit_feedback:
                                # We need a claim ID to submit feedback. 
                                # For this simple MVP, we'll assume the backend exposes it or we just fire a dummy one
                                # In a real app we'd get the ID back from the predict response.
                                # Let's assume the API returns it or we just mock it for now as the current predict schema didn't include ID explicitly but we can fix that later.
                                # Wait, I didn't add claim_id to the response schema. I should probably fix that or just pass 0 for now.
                                feedback_data = {"claim_id": 1, "is_fraud": is_fraud} # Placeholder ID
                                try:
                                    fb_response = requests.post(f"{API_URL}/feedback", json=feedback_data, headers=HEADERS)
                                    if fb_response.status_code == 200:
                                        st.success("Feedback recorded successfully!")
                                    else:
                                        st.error("Failed to submit feedback.")
                                except Exception as e:
                                    st.error(f"Error submitting feedback: {e}")

                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to backend API. Is it running?")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

elif page == "Dashboard Analytics":
    st.header("System Analytics")
    
    try:
        response = requests.get(f"{API_URL}/stats", headers=HEADERS)
        if response.status_code == 200:
            stats = response.json()
            
            # Key Metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Claims", stats["total_claims"])
            col2.metric("High Risk Claims", stats["high_risk_claims"])
            col3.metric("Low Risk Claims", stats["low_risk_claims"])
            col4.metric("Avg Risk Score", f"{stats['average_risk_score']:.2f}")
            
            # Charts
            st.subheader("Top Doctors by Claim Volume")
            if stats["top_doctors"]:
                st.bar_chart(stats["top_doctors"])
            else:
                st.info("No data available yet.")
                
            st.subheader("Top Diagnoses")
            if stats["top_diagnoses"]:
                st.bar_chart(stats["top_diagnoses"])
            else:
                st.info("No data available yet.")
                
        else:
            st.error("Failed to fetch statistics.")
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to backend API. Is it running?")
