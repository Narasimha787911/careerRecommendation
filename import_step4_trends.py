import logging
import numpy as np
import time
from datetime import datetime, timedelta
from app import app, db
from models import Career, MarketTrend
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_salary_range(base_salary=50000, growth_percentage=None):
    """Generate a salary range string based on base salary and growth percentage"""
    if growth_percentage is None:
        growth_percentage = np.random.uniform(2, 8)  # Default growth 2-8%
    
    # Calculate upper end of the range
    upper_salary = int(base_salary * (1 + growth_percentage/100))
    
    # Format as range string
    return f"{base_salary}-{upper_salary}"

def import_trends():
    """Import market trends for careers"""
    try:
        # Use direct SQL to get career IDs to avoid model mapping issues
        result = db.session.execute(text("SELECT id, name FROM career"))
        careers = [(row.id, row.name) for row in result]
        
        logger.info(f"Found {len(careers)} careers in database")
        
        # Import trends in batches
        trend_count = 0
        batch_size = 10
        
        logger.info(f"Importing trends for {len(careers)} careers in batches of {batch_size}...")
        
        for i in range(0, len(careers), batch_size):
            batch = careers[i:i+batch_size]
            
            # Process this batch
            for career_id, career_name in batch:
                # Generate a single market trend for this career
                # In a real app, we'd have multiple trends over time
                
                # Calculate demand level (0.1 to 0.9 scale)
                demand_level = max(0.1, min(0.9, np.random.normal(0.6, 0.2)))
                
                # Generate a salary range
                base_salary = int(30000 + 40000 * demand_level)  # Higher demand = higher salary
                growth_percentage = np.random.uniform(2, 8)  # Random growth 2-8%
                salary_range = generate_salary_range(base_salary, growth_percentage)
                
                # Create the trend record
                trend = MarketTrend(
                    career_id=career_id,
                    demand_level=demand_level,
                    salary_range=salary_range,
                    updated_at=datetime.utcnow()
                )
                
                db.session.add(trend)
                trend_count += 1
            
            # Commit this batch
            db.session.commit()
            logger.info(f"Imported trends for {min(i + batch_size, len(careers))} of {len(careers)} careers")
            
            # Brief pause to avoid overwhelming the database
            time.sleep(0.3)
        
        logger.info(f"Successfully imported {trend_count} market trends")
        return True
    
    except Exception as e:
        logger.error(f"Error importing trends: {e}")
        db.session.rollback()
        return False

def import_trends_chunk(start_index=0, end_index=None, chunk_size=20):
    """Import market trends for a specific chunk of careers"""
    try:
        # Use direct SQL to get career IDs to avoid model mapping issues
        result = db.session.execute(text("SELECT id, name FROM career"))
        all_careers = [(row.id, row.name) for row in result]
        
        # Determine the range to process
        if end_index is None:
            end_index = min(start_index + chunk_size, len(all_careers))
        else:
            end_index = min(end_index, len(all_careers))
        
        # Process only the specified chunk
        careers = all_careers[start_index:end_index]
        logger.info(f"Processing market trends for careers {start_index} to {end_index} of {len(all_careers)}")
        
        # Process small batches
        trend_count = 0
        for career_id, career_name in careers:
            # Calculate demand level (0.1 to 0.9 scale)
            demand_level = max(0.1, min(0.9, np.random.normal(0.6, 0.2)))
            
            # Generate a salary range
            base_salary = int(30000 + 40000 * demand_level)  # Higher demand = higher salary
            growth_percentage = np.random.uniform(2, 8)  # Random growth 2-8%
            salary_range = generate_salary_range(base_salary, growth_percentage)
            
            # Create the trend record
            trend = MarketTrend(
                career_id=career_id,
                demand_level=demand_level,
                salary_range=salary_range,
                updated_at=datetime.utcnow()
            )
            
            db.session.add(trend)
            trend_count += 1
            
            # Commit after each career's trends
            db.session.commit()
            logger.info(f"Imported trend for career {career_name} (ID: {career_id})")
            
            # Brief pause to avoid overwhelming the database
            time.sleep(0.1)
        
        logger.info(f"Successfully imported {trend_count} market trends for {len(careers)} careers")
        return True
    
    except Exception as e:
        logger.error(f"Error importing trends chunk: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    logger.info("Starting trends import step...")
    
    with app.app_context():
        # If a specific range is provided as arguments, process just that range
        import sys
        if len(sys.argv) > 1:
            start_idx = int(sys.argv[1])
            end_idx = int(sys.argv[2]) if len(sys.argv) > 2 else None
            
            if import_trends_chunk(start_idx, end_idx):
                logger.info(f"Trends chunk {start_idx} to {end_idx or 'end'} successfully imported")
            else:
                logger.error(f"Failed to import trends chunk {start_idx} to {end_idx or 'end'}")
        else:
            # Otherwise, try to import all trends
            if import_trends():
                logger.info("All market trends successfully imported")
            else:
                logger.error("Failed to import market trends")