#!/bin/bash

# Kill any existing Python processes
pkill -f "python main.py" || true

# Wait a moment to ensure processes are terminated
sleep 1

# Start the application in the background
nohup python main.py > flask_app.log 2>&1 &

# Echo the status
echo "Flask application restarted"
echo "Run 'tail -f flask_app.log' to view logs"