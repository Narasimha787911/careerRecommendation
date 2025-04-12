#!/bin/bash

echo "===== Starting Import Process ====="

# Step 1: Clear database
echo "Step 1: Clearing database..."
python import_step1_clear.py
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to clear database. Continuing anyway..."
fi

# Step 2: Import skills
echo "Step 2: Importing skills..."
python import_step2_skills.py
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to import skills. Exiting."
    exit 1
fi

# Step 3: Import careers
echo "Step 3: Importing careers..."
python import_step3_careers.py
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to import careers. Exiting."
    exit 1
fi

# Step 4: Import market trends
echo "Step 4: Importing market trends..."
python import_step4_trends.py
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to import market trends. Exiting."
    exit 1
fi

echo "===== Import Process Completed Successfully ====="