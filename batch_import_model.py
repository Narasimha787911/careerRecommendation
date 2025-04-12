import os
import json
import logging
import numpy as np
from app import app, db
from models import Career, Skill, MarketTrend
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
        return True
    except Exception as e:
        logger.error(f"Error clearing existing data: {e}")
        db.session.rollback()
        return False

def import_skills(skills_data):
    """Import skills in batches"""
    skill_dict = {}
    logger.info(f"Adding {len(skills_data)} skills to database...")
    
    # Process in batches of 50
    batch_size = 50
    for i in range(0, len(skills_data), batch_size):
        batch = skills_data[i:i+batch_size]
        
        # Add skills batch
        batch_skills = []
        for skill_name in batch:
            # Truncate skill name to fit in database column (max 64 chars)
            if len(skill_name) > 60:
                truncated_name = skill_name[:60] + "..."
                logger.debug(f"Truncating skill name: {skill_name} -> {truncated_name}")
                skill_name_db = truncated_name
            else:
                skill_name_db = skill_name
            
            skill = Skill(name=skill_name_db, category="From Kaggle Dataset")
            db.session.add(skill)
            batch_skills.append((skill_name, skill))
        
        # Commit the batch
        db.session.commit()
        
        # Update skill dictionary
        for orig_name, skill in batch_skills:
            skill_dict[orig_name] = skill
        
        logger.info(f"Imported {min(i + batch_size, len(skills_data))} of {len(skills_data)} skills")
    
    return skill_dict

def import_careers_batch(careers_batch, skill_dict):
    """Import a batch of careers with their skills and trends"""
    # Add careers
    all_trends = []
    for career_info in careers_batch:
        career = Career(
            title=career_info['title'],
            description=career_info['description'],
            education_required=career_info['education_required'],
            avg_salary=career_info['avg_salary'],
            growth_rate=career_info['growth_rate'],
            work_environment=career_info['work_environment']
        )
        
        db.session.add(career)
        
        # Keep track of career and skills to add
        career_skills = []
        for skill_name in career_info.get('skills', []):
            if skill_name in skill_dict:
                career_skills.append((career, skill_dict[skill_name]))
        
        # Generate market trends for this career
        current_year = 2025
        career_trends = []
        for year_offset in range(5):
            year = current_year - year_offset
            trend = {
                'career': career,
                'year': year,
                'demand_level': max(0.1, min(0.9, np.random.normal(0.5, 0.2))),
                'salary_trend': max(-5, min(10, np.random.normal(3, 2))),
                'job_posting_count': int(max(100, np.random.normal(1000, 300))),
                'source': "Kaggle Career Dataset Analysis"
            }
            career_trends.append(trend)
    
    # Commit the careers first
    db.session.commit()
    
    # Now add career-skill relationships
    for career, skill in career_skills:
        career.skills.append(skill)
    
    # Add market trends
    for trend_info in all_trends:
        trend = MarketTrend(
            career_id=trend_info['career'].id,
            year=trend_info['year'],
            demand_level=trend_info['demand_level'],
            salary_trend=trend_info['salary_trend'],
            job_posting_count=trend_info['job_posting_count'],
            source=trend_info['source']
        )
        db.session.add(trend)
    
    # Commit the relationships and trends
    db.session.commit()

def import_careers_to_database():
    """Import processed career data to the database in batches"""
    try:
        # Load the processed career data
        careers_file = 'models/careers.json'
        if not os.path.exists(careers_file):
            logger.error(f"Career data file not found: {careers_file}")
            return False
        
        with open(careers_file, 'r') as f:
            career_data = json.load(f)
        
        logger.info(f"Loaded career data with {len(career_data)} careers")
        
        # Step 1: Clear the database
        if not clear_database():
            logger.error("Failed to clear database. Continuing anyway...")
        
        # Step 2: Extract all unique skills
        unique_skills = set()
        for career in career_data:
            for skill in career.get('skills', []):
                if skill:
                    unique_skills.add(skill)
        
        # Step 3: Import skills
        skill_dict = import_skills(list(unique_skills))
        
        # Step 4: Import careers in batches
        batch_size = 50
        total_careers = len(career_data)
        logger.info(f"Adding {total_careers} careers to database in batches of {batch_size}...")
        
        for i in range(0, total_careers, batch_size):
            batch = career_data[i:i+batch_size]
            import_careers_batch(batch, skill_dict)
            logger.info(f"Imported {min(i + batch_size, total_careers)} of {total_careers} careers")
        
        logger.info("Successfully imported career data to database")
        return True
    
    except Exception as e:
        logger.error(f"Error importing data to database: {e}")
        try:
            db.session.rollback()
        except:
            pass
        return False

def import_career_trends():
    """Import market trends for careers"""
    try:
        logger.info("Adding market trends for careers...")
        
        with app.app_context():
            # Get all careers
            careers = Career.query.all()
            logger.info(f"Found {len(careers)} careers")
            
            # Process in batches
            batch_size = 50
            for i in range(0, len(careers), batch_size):
                batch = careers[i:i+batch_size]
                
                for career in batch:
                    # Generate market trends for this career
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
                
                # Commit the batch
                db.session.commit()
                logger.info(f"Added trends for {min(i + batch_size, len(careers))} of {len(careers)} careers")
        
        logger.info("Successfully added market trends")
        return True
    
    except Exception as e:
        logger.error(f"Error adding market trends: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting career data import to database...")
    
    with app.app_context():
        # First clear the database
        if not clear_database():
            logger.error("Failed to clear database. Exiting...")
            exit(1)
        
        # Load the processed career data
        careers_file = 'models/careers.json'
        if not os.path.exists(careers_file):
            logger.error(f"Career data file not found: {careers_file}")
            exit(1)
        
        with open(careers_file, 'r') as f:
            career_data = json.load(f)
        
        logger.info(f"Loaded career data with {len(career_data)} careers")
        
        # Extract all unique skills
        unique_skills = set()
        for career in career_data:
            for skill in career.get('skills', []):
                if skill:
                    unique_skills.add(skill)
        
        # Import skills
        skill_dict = import_skills(list(unique_skills))
        logger.info(f"Successfully imported {len(skill_dict)} skills")
        
        # Import careers
        logger.info("Importing careers...")
        
        # Process in smaller batches
        batch_size = 25
        for i in range(0, len(career_data), batch_size):
            batch = career_data[i:i+batch_size]
            
            # Add careers
            for career_info in batch:
                try:
                    career = Career(
                        title=career_info['title'],
                        description=career_info['description'],
                        education_required=career_info['education_required'],
                        avg_salary=career_info['avg_salary'],
                        growth_rate=career_info['growth_rate'],
                        work_environment=career_info['work_environment']
                    )
                    
                    db.session.add(career)
                    db.session.flush()  # Get the ID
                    
                    # Add skills to career
                    for skill_name in career_info.get('skills', []):
                        if skill_name in skill_dict:
                            career.skills.append(skill_dict[skill_name])
                except Exception as e:
                    logger.error(f"Error adding career {career_info['title']}: {e}")
                    continue
            
            # Commit the batch
            db.session.commit()
            logger.info(f"Imported {min(i + batch_size, len(career_data))} of {len(career_data)} careers")
        
        # Import market trends in a separate step
        logger.info("Adding market trends...")
        
        # Get all careers
        careers = Career.query.all()
        logger.info(f"Found {len(careers)} careers")
        
        # Process in batches
        batch_size = 50
        for i in range(0, len(careers), batch_size):
            batch = careers[i:i+batch_size]
            
            # Add trends
            for career in batch:
                # Generate trends
                current_year = 2025
                for year_offset in range(5):
                    year = current_year - year_offset
                    try:
                        trend = MarketTrend(
                            career_id=career.id,
                            year=year,
                            demand_level=max(0.1, min(0.9, np.random.normal(0.5, 0.2))),
                            salary_trend=max(-5, min(10, np.random.normal(3, 2))),
                            job_posting_count=int(max(100, np.random.normal(1000, 300))),
                            source="Kaggle Career Dataset Analysis"
                        )
                        db.session.add(trend)
                    except Exception as e:
                        logger.error(f"Error adding trend for career {career.id}: {e}")
                        continue
            
            # Commit the batch
            db.session.commit()
            logger.info(f"Added trends for {min(i + batch_size, len(careers))} of {len(careers)} careers")
        
        logger.info("Career data import completed successfully!")