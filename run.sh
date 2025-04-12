#!/bin/bash

# Kill any existing Python processes
pkill -f "python main.py" || true

# Run the Flask app
echo "Starting Flask application..."
python main.py