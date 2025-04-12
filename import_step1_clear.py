import logging
from app import app, db
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clear_database():
    """Clear existing data with proper foreign key handling"""
    try:
        # Delete related records first to address foreign key constraints
        logger.info("Clearing existing data with foreign key constraints...")
        
        # Delete recommendations first (they reference careers)
        db.session.execute(text("DELETE FROM recommendation"))
        logger.info("Cleared recommendations")
        
        # Delete market trends (they reference careers)
        db.session.execute(text("DELETE FROM market_trend"))
        logger.info("Cleared market trends")
        
        # Delete career_skill associations
        db.session.execute(text("DELETE FROM career_skill"))
        logger.info("Cleared career_skill associations")
        
        # Delete careers
        db.session.execute(text("DELETE FROM career"))
        logger.info("Cleared careers")
        
        # Delete skills
        db.session.execute(text("DELETE FROM skill"))
        logger.info("Cleared skills")
        
        db.session.commit()
        logger.info("Successfully cleared existing data")
        return True
    except Exception as e:
        logger.error(f"Error clearing existing data: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    logger.info("Starting database clearing step...")
    
    with app.app_context():
        if clear_database():
            logger.info("Database successfully cleared")
        else:
            logger.error("Failed to clear database")