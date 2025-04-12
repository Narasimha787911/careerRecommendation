#!/bin/bash

# Run in background to prevent timeout
nohup python main.py > flask_app.log 2>&1 &

# Output the log file to track startup
sleep 2
tail -f flask_app.log