#!/bin/bash

# Set environment variables
export FLASK_APP=main.py
export FLASK_DEBUG=1
export PYTHONPATH=.

# Run the Flask application
python main.py