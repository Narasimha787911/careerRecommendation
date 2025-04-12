#!/bin/bash

echo "==== Career Recommendation Model Training and Import ===="

# Create necessary directories
mkdir -p data models

# Copy dataset if needed
if [ ! -f "data/career_recommender.csv" ]; then
  echo "Copying career dataset..."
  cp attached_assets/career_recommender.csv data/
fi

# Process the dataset and train the model
echo "Processing dataset and training model..."
python train_kaggle_model.py

# Wait for model training to complete
sleep 2

# Import the model data to database
echo "Importing model data to database..."
python import_model_to_db.py

echo "==== Training and Import Completed ===="