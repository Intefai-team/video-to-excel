import streamlit as st
import requests
import time
import os

# Configuration - Updated to your Render URL
FLASK_URL = os.getenv("FLASK_URL", "https://video-ypj7.onrender.com")

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

# Backend status check - Modified to check root endpoint since you don't have /health
with st.expander("Backend Status", expanded=False):
    try:
        # Try accessing the root endpoint or any valid endpoint
        test_response = requests.get(FLASK_URL, timeout=2)
        if test_response.status_code in [200, 404, 405]:  # 405 is Method Not Allowed (which means endpoint exists)
            st.success(f"✅ Backend service is available at {FLASK_URL}")
        else:
            st.error(f"❌ Backend service returned status {test_response.status_code}")
    except Exception as e:
        st.error(f"❌ Could not connect to backend at {FLASK_URL}")
        st.error(f"Error details: {str(e)}")

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
                
                # Updated to use your actual endpoint
                response = requests.post(
                    f"{FLASK_URL}/transcribe",
                    files=files,
                    timeout=300  # 5 minutes timeout for longer videos
                )
                
                if response.status_code != 200:
                    error_msg = response.json().get('error', 'Unknown error')
                    st.error(f"Error: {error_msg}")
                    
                    # Special handling for FFmpeg errors
                    if "ffmpeg" in error_msg.lower():
                        st.warning("""
                        **FFmpeg is required for audio extraction.**  
                        This backend service should have FFmpeg installed.  
                        If you're seeing this error, please contact support.
                        """)
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
                    
                    # Download button - Updated to match your backend
                    st.markdown("---")
                    st.markdown("### Download Results")
                    
                    if st.button("📥 Download Excel", key="download", 
                                help="Download the transcription as Excel file",
                                type="primary"):
                        with st.spinner("Generating Excel file..."):
                            try:
                                excel_response = requests.post(
                                    f"{FLASK_URL}/download_excel",
                                    json={
                                        "extracted_info": result.get("extracted_info", {}),
                                        "transcription": result.get("transcription", "")
                                    },
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
                                    st.error(f"Failed to generate Excel file: {excel_response.text}")
                            except Exception as e:
                                st.error(f"Error downloading Excel: {str(e)}")
            except requests.exceptions.Timeout:
                st.error("""
                Processing took too long. Please try:
                - A shorter video (under 2 minutes)
                - A video with clearer audio
                - Checking backend status above
                """)
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

### ⚠️ Important Notes:
- Backend is hosted on Render's free tier (may be slow to start)
- First request after inactivity may take 30-60 seconds
- Maximum recommended video length: 2 minutes for free tier
- For better performance, use videos with clear English speech
""")
