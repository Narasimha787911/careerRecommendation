#!/bin/bash

echo "==== Career Recommendation Model Training and Testing ===="

# Create necessary directories
mkdir -p data models

# Process the dataset and train the model
echo "Processing dataset and training model..."
python process_career_dataset.py

# Wait for model training to complete
sleep 2

# Test the model
echo "Testing the trained model..."
python test_model.py

echo "==== Training and Testing Completed ===="