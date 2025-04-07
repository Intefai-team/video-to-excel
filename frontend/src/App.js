import React, { useState } from "react";
import axios from "axios";
import "./styles.css";
import fileImage from "./file.png"; // Import the image

const VideoTranscriptionApp = () => {
  const [file, setFile] = useState(null);
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Please select a video file.");
      return;
    }

    const formData = new FormData();
    formData.append("video", file);

    try {
      setLoading(true);
      setResponse(null); // Reset previous transcription

      const res = await axios.post("http://127.0.0.1:5000/transcribe", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setResponse(res.data);
    } catch (error) {
      console.error("Error uploading video:", error);
      setResponse({ error: "Failed to process video." });
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadExcel = async () => {
    if (!response || !response.transcription) {
      alert("No transcription available to download.");
      return;
    }

    try {
      setDownloading(true);
      
      const res = await axios.post("http://127.0.0.1:5000/download_excel", response, {
        responseType: "blob",
      });

      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "transcription_data.xlsx");
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error("Error downloading Excel:", error);
      alert("Failed to download Excel file.");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="container">
      {/* Add the image above the heading */}
      <div className="app-header">
        <img src={fileImage} alt="Video Transcription" className="app-logo" />
        <h1>Video Transcription App</h1>
      </div>
      
      <input type="file" accept="video/*" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={loading}>
        {loading ? "Uploading..." : "Upload & Transcribe"}
      </button>

      {response && (
        <div className="output">
          <h2>Transcription</h2>
          <p>{response.transcription || response.error}</p>
          {response.transcription && (
            <button onClick={handleDownloadExcel} className="download-btn" disabled={downloading}>
              {downloading ? "Downloading..." : "Download Excel"}
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default VideoTranscriptionApp;