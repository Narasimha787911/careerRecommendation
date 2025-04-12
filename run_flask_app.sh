#!/bin/bash

# Kill any existing Python processes
pkill -f "python main.py" || true

# Wait a moment to ensure processes are terminated
sleep 2

# Start the Flask application
echo "Starting Flask application..."
# Run in the foreground instead of background
exec python main.py