import os
import json
import logging
import numpy as np
from app import app, db
from models import Career, Skill, MarketTrend, Recommendation, career_skill
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_careers_to_database():
    """Import processed career data to the database"""
    try:
        # Load the processed career data
        careers_file = 'models/careers.json'
        if not os.path.exists(careers_file):
            logger.error(f"Career data file not found: {careers_file}")
            return False
        
        with open(careers_file, 'r') as f:
            career_data = json.load(f)
        
        logger.info(f"Loaded career data with {len(career_data)} careers")
        
        with app.app_context():
            # Create skill dictionary
            unique_skills = set()
            
            for career in career_data:
                for skill in career.get('skills', []):
                    if skill:
                        unique_skills.add(skill)
            
            # Delete related records first to address foreign key constraints
            logger.info("Clearing existing data with foreign key constraints...")
            try:
                # Delete recommendations first (they reference careers)
                db.session.execute(text("DELETE FROM recommendation"))
                
                # Delete market trends (they reference careers)
                db.session.execute(text("DELETE FROM market_trend"))
                
                # Delete career_skill associations
                db.session.execute(text("DELETE FROM career_skill"))
                
                # Delete careers
                db.session.execute(text("DELETE FROM career"))
                
                # Delete skills
                db.session.execute(text("DELETE FROM skill"))
                
                db.session.commit()
                logger.info("Successfully cleared existing data")
            except Exception as e:
                logger.error(f"Error clearing existing data: {e}")
                db.session.rollback()
                # Continue with import anyway
            
            # Add skills to database
            skill_dict = {}
            logger.info(f"Adding {len(unique_skills)} skills to database...")
            
            for skill_name in unique_skills:
                # Truncate skill name to fit in database column (max 64 chars)
                if len(skill_name) > 60:
                    truncated_name = skill_name[:60] + "..."
                    logger.warning(f"Truncating skill name: {skill_name} -> {truncated_name}")
                    skill_name_db = truncated_name
                else:
                    skill_name_db = skill_name
                
                skill = Skill(name=skill_name_db, category="From Kaggle Dataset")
                db.session.add(skill)
                db.session.flush()
                skill_dict[skill_name] = skill
            
            # Add careers to database
            logger.info(f"Adding {len(career_data)} careers to database...")
            
            for career_info in career_data:
                career = Career(
                    title=career_info['title'],
                    description=career_info['description'],
                    education_required=career_info['education_required'],
                    avg_salary=career_info['avg_salary'],
                    growth_rate=career_info['growth_rate'],
                    work_environment=career_info['work_environment']
                )
                
                db.session.add(career)
                
                # Add skills to career
                for skill_name in career_info.get('skills', []):
                    if skill_name in skill_dict:
                        career.skills.append(skill_dict[skill_name])
                
                db.session.flush()
                
                # Add market trends
                current_year = 2025
                for year_offset in range(5):
                    year = current_year - year_offset
                    trend = MarketTrend(
                        career_id=career.id,
                        year=year,
                        demand_level=max(0.1, min(0.9, np.random.normal(0.5, 0.2))),
                        salary_trend=max(-5, min(10, np.random.normal(3, 2))),
                        job_posting_count=int(max(100, np.random.normal(1000, 300))),
                        source="Kaggle Career Dataset Analysis"
                    )
                    db.session.add(trend)
            
            db.session.commit()
            logger.info("Successfully imported career data to database")
            return True
    
    except Exception as e:
        logger.error(f"Error importing data to database: {e}")
        try:
            db.session.rollback()
        except:
            pass
        return False

if __name__ == "__main__":
    logger.info("Starting career data import to database...")
    
    with app.app_context():
        success = import_careers_to_database()
    
    if success:
        logger.info("Career data import completed successfully!")
    else:
        logger.error("Career data import failed!")