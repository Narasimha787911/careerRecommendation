#!/bin/bash
# AI Career Recommendation System Launcher
# This script is designed to start the Career Recommendation System
# and keep it running even if the Replit environment resets

echo "⭐️ Starting AI Career Recommendation System ⭐️"
echo "----------------------------------------------"
echo "$(date): System startup initiated"

# Set environment variables if needed
export FLASK_APP=main.py
export FLASK_DEBUG=1

# Run the Flask application
echo "Starting Flask server on port 5000..."
exec python main.py