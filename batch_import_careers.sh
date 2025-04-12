#!/bin/bash

# Number of careers to import in each batch
BATCH_SIZE=20
# Total careers to import (from total of 448)
TOTAL_CAREERS=100

# First clear the database (except for already imported careers and skills)
echo "== Starting batch import process for $TOTAL_CAREERS careers =="

# Import careers in batches
echo "== Importing careers in batches of $BATCH_SIZE =="
for ((i=10; i<$TOTAL_CAREERS; i+=$BATCH_SIZE)); do
    end=$((i + BATCH_SIZE))
    if [ $end -gt $TOTAL_CAREERS ]; then
        end=$TOTAL_CAREERS
    fi
    
    echo "== Importing careers batch $i to $end =="
    python import_step3_careers.py $i $end
    
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to import careers batch $i to $end. Stopping."
        exit 1
    fi
    
    # Give a short pause between batches
    sleep 2
done

# Import market trends for the newly imported careers
echo "== Importing market trends in batches of $BATCH_SIZE =="
for ((i=10; i<$TOTAL_CAREERS; i+=$BATCH_SIZE)); do
    end=$((i + BATCH_SIZE))
    if [ $end -gt $TOTAL_CAREERS ]; then
        end=$TOTAL_CAREERS
    fi
    
    echo "== Importing trends batch $i to $end =="
    python import_step4_trends.py $i $end
    
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to import trends batch $i to $end. Stopping."
        exit 1
    fi
    
    # Give a short pause between batches
    sleep 2
done

echo "== Import process completed successfully! =="
echo "Imported $TOTAL_CAREERS careers with their market trends."