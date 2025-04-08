from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
import torch
import whisper
import subprocess
import re
import pandas as pd
import gc
import logging
from moviepy.video.io.VideoFileClip import VideoFileClip

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Disable unnecessary logging
logging.getLogger("moviepy").setLevel(logging.WARNING)

def load_whisper_model():
    try:
        # Force CPU to save memory (comment out if you have GPU)
        device = "cpu"  # Changed from cuda to cpu
        logger.info(f"Loading Whisper model on {device}")
        
        # Load smaller model but keep functionality
        model = whisper.load_model("small", device=device)  # Changed from base to small
        
        # Memory optimization
        if device == "cpu":
            torch.set_num_threads(1)  # Limit CPU threads
            
        logger.info("Model loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        return None

whisper_model = load_whisper_model()

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, 
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def extract_audio(video_path, max_duration=180):  # Reduced from 300 to 180 seconds
    audio_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            audio_path = temp_audio.name
        
        with VideoFileClip(video_path) as clip:
            if clip.audio is None:
                return None, "No audio stream found"
                
            if clip.duration > max_duration:
                return None, f"Video exceeds {max_duration} second limit"
                
            # Optimized audio extraction
            clip.audio.write_audiofile(
                audio_path, 
                codec="pcm_s16le", 
                fps=16000,
                logger=None,
                ffmpeg_params=["-ac", "1"]  # Mono audio to save memory
            )
        
        return audio_path, None
    except Exception as e:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
        return None, f"Audio extraction error: {str(e)}"

def transcribe_audio(audio_path):
    try:
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            return None, "Invalid audio file"
            
        if whisper_model is None:
            return None, "Whisper model not loaded"
            
        # Optimized transcription
        result = whisper_model.transcribe(
            audio_path,
            language="en",
            fp16=False,
            task="transcribe"  # Explicitly set to transcribe
        )
        return result["text"], None
    except Exception as e:
        return None, f"Transcription error: {str(e)}"

def extract_info(text):
    data = {"name": None, "location": None}
    
    # Pre-compile regex patterns for better performance
    name_patterns = [
        re.compile(r"(?:hi|hello|hey)[, ]*(?:this is me|i am|my name is|myself) ([A-Z][a-z]+)", re.IGNORECASE),
        re.compile(r"\bthis is me[, ]*([A-Z][a-z]+)\b", re.IGNORECASE),
        re.compile(r"\bmy name is ([A-Z][a-z]+)\b", re.IGNORECASE),
        re.compile(r"\bi am ([A-Z][a-z]+)\b", re.IGNORECASE)
    ]
    
    location_patterns = [
        re.compile(r"\b(?:i'm from|i live in|i am from) ([A-Z][a-z]+)\b", re.IGNORECASE),
        re.compile(r"\b(?:in|from) ([A-Z][a-z]+)(?:,|\s|$)", re.IGNORECASE),
        re.compile(r"\bdid \w+ in ([A-Z][a-z]+)\b", re.IGNORECASE),
        re.compile(r"\bmoved to ([A-Z][a-z]+)\b", re.IGNORECASE)
    ]
    
    for pattern in name_patterns:
        match = pattern.search(text)
        if match:
            name = match.group(1).strip()
            if name.lower() in ["pyle", "pail", "pyl"]:
                data["name"] = "Payal"
            else:
                data["name"] = name
            break
    
    for pattern in location_patterns:
        match = pattern.search(text)
        if match:
            data["location"] = match.group(1).strip()
            break
    
    return data

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "whisper_loaded": whisper_model is not None,
        "ffmpeg_available": check_ffmpeg()
    })

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400
        
    file = request.files["video"]
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi')):
        return jsonify({"error": "Invalid file type"}), 400
    
    video_path = None
    audio_path = None
    
    try:
        # Save video
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
            video_path = f.name
            file.save(f.name)
            
        # Process audio
        audio_path, audio_error = extract_audio(video_path)
        if audio_error:
            raise Exception(audio_error)
            
        # Transcribe
        transcription, transcribe_error = transcribe_audio(audio_path)
        if transcribe_error:
            raise Exception(transcribe_error)
            
        # Extract info
        extracted = extract_info(transcription)
        
        return jsonify({
            "transcription": transcription,
            "extracted_info": extracted
        })
        
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        # Enhanced cleanup with memory management
        for path in [video_path, audio_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    logger.warning(f"Could not remove {path}: {str(e)}")
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

@app.route("/download_excel", methods=["POST"])
def download_excel():
    excel_path = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Optimized DataFrame creation
        df = pd.DataFrame([{
            "Name": data.get("extracted_info", {}).get("name", "N/A"),
            "Location": data.get("extracted_info", {}).get("location", "N/A"),
            "Full Transcription": data.get("transcription", "")
        }])
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as f:
            excel_path = f.name
            df.to_excel(excel_path, index=False, engine='openpyxl')  # Specify engine
            
        return send_file(
            excel_path,
            as_attachment=True,
            download_name="transcription_report.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        logger.error(f"Excel generation error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if excel_path and os.path.exists(excel_path):
            try:
                os.remove(excel_path)
            except Exception as e:
                logger.warning(f"Could not remove {excel_path}: {str(e)}")
        gc.collect()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
