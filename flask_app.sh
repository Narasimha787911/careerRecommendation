#!/bin/bash

# Kill any existing Flask processes 
pkill -f "python main.py" 2>/dev/null || true

# Set environment variables
export FLASK_APP=main.py
export FLASK_DEBUG=1
export PYTHONPATH=.

# Clear any existing log
> flask_app.log

# Start the application in the foreground
exec python main.py