#!/bin/bash

# Start Flask backend in background
python app.py &

# Wait for Flask to start (adjust time as needed)
sleep 3

# Start Streamlit frontend
streamlit run streamlit_app.py --server.enableCORS false --server.enableXsrfProtection false
