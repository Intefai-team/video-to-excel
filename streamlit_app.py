import streamlit as st
import requests
import time
import os

# Configuration
FLASK_URL = os.getenv("FLASK_URL", "https://video-to-excel.onrender.com")

# Set page config
st.set_page_config(
    page_title="Video Transcription App",
    page_icon="🎥",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .download-btn {
        background-color: #2196F3 !important;
    }
    .download-btn:hover {
        background-color: #0b7dda !important;
    }
    .output-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin-top: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .stVideo {
        border-radius: 10px;
        max-width: 400px !important;
        margin: 0 auto;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .success-msg {
        color: #4CAF50;
        font-weight: bold;
    }
    .error-msg {
        color: #f44336;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# App header
st.markdown("""
<div class="header">
    <h1>🎥 Video Transcription App</h1>
    <p>Upload a video to extract audio and transcribe it</p>
</div>
""", unsafe_allow_html=True)

# Backend status
with st.expander("Backend Status", expanded=False):
    try:
        health_response = requests.get(f"{FLASK_URL}/health", timeout=2)
        if health_response.status_code == 200:
            st.success(f"✅ Backend service is available at {FLASK_URL}")
            st.json(health_response.json())
        else:
            st.error(f"❌ Backend service unavailable at {FLASK_URL}")
    except:
        st.error(f"❌ Could not connect to backend at {FLASK_URL}")

# File uploader
uploaded_file = st.file_uploader(
    "Choose a video file (MP4, MOV, AVI)",
    type=["mp4", "mov", "avi"],
    accept_multiple_files=False
)

if uploaded_file is not None:
    # Display the uploaded video
    st.markdown("### Your Video Preview")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.video(uploaded_file, format="video/mp4", start_time=0)
    
    if st.button("🚀 Upload & Transcribe", key="transcribe"):
        with st.spinner("🔍 Processing video... This may take a few minutes..."):
            try:
                files = {"video": uploaded_file}
                start_time = time.time()
                
                response = requests.post(
                    f"{FLASK_URL}/transcribe",
                    files=files,
                    timeout=300
                )
                
                if response.status_code != 200:
                    st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                else:
                    result = response.json()
                    processing_time = time.time() - start_time
                    
                    st.markdown(f'<p class="success-msg">✅ Transcription completed in {processing_time:.2f} seconds!</p>', 
                               unsafe_allow_html=True)
                    
                    # Show extracted info
                    with st.expander("📋 Extracted Information", expanded=True):
                        st.json(result.get("extracted_info", {}))
                    
                    # Show full transcription
                    with st.expander("📝 Full Transcription", expanded=False):
                        st.write(result.get("transcription", ""))
                    
                    # Download button
                    st.markdown("---")
                    st.markdown("### Download Results")
                    
                    if st.button("📥 Download Excel", key="download", 
                                help="Download the transcription as Excel file",
                                type="primary"):
                        with st.spinner("Generating Excel file..."):
                            try:
                                excel_response = requests.post(
                                    f"{FLASK_URL}/download_excel",
                                    json=result,
                                    headers={"Content-Type": "application/json"},
                                    timeout=60
                                )
                                
                                if excel_response.status_code == 200:
                                    st.download_button(
                                        label="⬇️ Click to download Excel",
                                        data=excel_response.content,
                                        file_name="transcription_data.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    )
                                else:
                                    st.error("Failed to generate Excel file")
                            except Exception as e:
                                st.error(f"Error downloading Excel: {str(e)}")
            except requests.exceptions.Timeout:
                st.error("Processing took too long. Please try a shorter video.")
            except Exception as e:
                st.error(f"Error processing video: {str(e)}")

# Instructions
st.markdown("""
---
### 📚 Instructions:
1. Upload a video file (MP4, MOV, AVI)
2. Click the "Upload & Transcribe" button
3. View the extracted information and full transcription
4. Download the results as an Excel file if needed

### ⚠️ Note:
- Video processing may take several minutes depending on length
- For best results, use videos with clear audio
- Maximum recommended video length: 5 minutes
""")
