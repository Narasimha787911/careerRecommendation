#!/bin/bash
# Stop any existing Flask process
pkill -f "python main.py" || true
echo "Starting Career Recommendation System..."
# Clear previous log
> flask_app.log
# Start the app in the background
nohup python -u main.py > flask_app.log 2>&1 &
pid=$!
echo "Application started with PID: $pid. Check flask_app.log for details."
# Give the app a moment to start up
sleep 3
# Check if the process is still running
if ps -p $pid > /dev/null; then
    echo "Application is running successfully."
    tail -n 5 flask_app.log
else
    echo "Application failed to start. Error log:"
    cat flask_app.log
fi