# streamlit_app.py (updated with smaller video display)
import streamlit as st
import requests
from io import BytesIO

# Set page config
st.set_page_config(
    page_title="Video Transcription App",
    page_icon="🎥",
    layout="centered"
)

# Custom CSS (updated with video styling)
st.markdown("""
<style>
    .stButton>button {
        background-color: #007bff;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #0056b3;
    }
    .download-btn {
        background-color: #28a745 !important;
    }
    .download-btn:hover {
        background-color: #218838 !important;
    }
    .output-box {
        background-color: #eef;
        padding: 1rem;
        border-radius: 10px;
        margin-top: 1rem;
    }
    .header {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 2rem;
    }
    /* Add this for smaller video */
    .stVideo {
        border-radius: 10px;
        max-width: 400px !important;
        margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)

# App header
st.markdown("""
<div class="header">
    <h1>Video Transcription App</h1>
</div>
""", unsafe_allow_html=True)

# File uploader
uploaded_file = st.file_uploader("Choose a video file", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    # Display the uploaded video in a smaller format
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.video(uploaded_file, format="video/mp4", start_time=0)
    
    if st.button("Upload & Transcribe"):
        with st.spinner("Processing video... This may take a few minutes..."):
            try:
                # Send to Flask backend
                files = {"video": uploaded_file}
                response = requests.post(
                    "http://127.0.0.1:5000/transcribe",
                    files=files
                ).json()
                
                if "error" in response:
                    st.error(response["error"])
                else:
                    st.success("Transcription completed!")
                    
                    # Show extracted info
                    st.subheader("Extracted Information")
                    st.json(response.get("extracted_info", {}))
                    
                    # Show full transcription
                    st.subheader("Full Transcription")
                    st.write(response.get("transcription", ""))
                    
                    # Download button
                    if st.button("Download Excel", key="download", 
                                help="Download the transcription as Excel file",
                                type="primary"):
                        with st.spinner("Generating Excel file..."):
                            try:
                                excel_response = requests.post(
                                    "http://127.0.0.1:5000/download_excel",
                                    json=response,
                                    headers={"Content-Type": "application/json"}
                                )
                                
                                if excel_response.status_code == 200:
                                    st.download_button(
                                        label="Click to download",
                                        data=excel_response.content,
                                        file_name="transcription_data.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    )
                                else:
                                    st.error("Failed to generate Excel file")
                            except Exception as e:
                                st.error(f"Error downloading Excel: {str(e)}")
            except Exception as e:
                st.error(f"Error processing video: {str(e)}")

# Instructions
st.markdown("""
### Instructions:
1. Upload a video file (MP4, MOV, AVI)
2. Click the "Upload & Transcribe" button
3. View the extracted information and full transcription
4. Download the results as an Excel file if needed
""")