import os
import json
import time
import logging
from app import app, db
from models import Skill

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_skills():
    """Import skills from career data"""
    try:
        # Load the processed career data
        careers_file = 'models/careers.json'
        if not os.path.exists(careers_file):
            logger.error(f"Career data file not found: {careers_file}")
            return False
        
        with open(careers_file, 'r') as f:
            career_data = json.load(f)
        
        logger.info(f"Loaded career data with {len(career_data)} careers")
        
        # Extract all unique skills
        unique_skills = set()
        for career in career_data:
            for skill in career.get('skills', []):
                if skill:
                    unique_skills.add(skill)
        
        # Import skills in very small batches with pauses
        skill_count = 0
        batch_size = 10  # Reduced batch size
        skills_list = list(unique_skills)
        
        logger.info(f"Importing {len(skills_list)} skills in batches of {batch_size}...")
        
        for i in range(0, len(skills_list), batch_size):
            batch = skills_list[i:i+batch_size]
            
            # Process this batch
            batch_additions = 0
            for skill_name in batch:
                # Truncate skill name to fit in database column (max 64 chars)
                if len(skill_name) > 60:
                    truncated_name = skill_name[:60] + "..."
                    skill_name_db = truncated_name
                else:
                    skill_name_db = skill_name
                
                # Check if skill already exists
                existing_skill = Skill.query.filter_by(name=skill_name_db).first()
                if not existing_skill:
                    skill = Skill(name=skill_name_db, category="From Kaggle Dataset")
                    db.session.add(skill)
                    skill_count += 1
                    batch_additions += 1
            
            # Only commit if we actually added something
            if batch_additions > 0:
                try:
                    db.session.commit()
                    logger.info(f"Imported {min(i + batch_size, len(skills_list))} of {len(skills_list)} skills")
                except Exception as e:
                    logger.error(f"Error committing batch: {e}")
                    db.session.rollback()
                    # Try one by one if batch commit fails
                    for skill_name in batch:
                        try:
                            if len(skill_name) > 60:
                                truncated_name = skill_name[:60] + "..."
                                skill_name_db = truncated_name
                            else:
                                skill_name_db = skill_name
                            
                            existing_skill = Skill.query.filter_by(name=skill_name_db).first()
                            if not existing_skill:
                                skill = Skill(name=skill_name_db, category="From Kaggle Dataset")
                                db.session.add(skill)
                                db.session.commit()
                                logger.info(f"Individually imported skill: {skill_name_db}")
                                skill_count += 1
                        except Exception as inner_e:
                            logger.error(f"Error importing individual skill {skill_name}: {inner_e}")
                            db.session.rollback()
            else:
                logger.info(f"No new skills to add in batch {i//batch_size + 1}")
            
            # Pause between batches to avoid overwhelming the database
            time.sleep(0.5)
        
        logger.info(f"Successfully imported {skill_count} skills")
        return True
    
    except Exception as e:
        logger.error(f"Error importing skills: {e}")
        db.session.rollback()
        return False

def import_skills_chunk(start_index=0, end_index=None, chunk_size=50):
    """Import a specific chunk of skills"""
    try:
        # Load the processed career data
        careers_file = 'models/careers.json'
        if not os.path.exists(careers_file):
            logger.error(f"Career data file not found: {careers_file}")
            return False
        
        with open(careers_file, 'r') as f:
            career_data = json.load(f)
        
        logger.info(f"Loaded career data with {len(career_data)} careers")
        
        # Extract all unique skills
        unique_skills = set()
        for career in career_data:
            for skill in career.get('skills', []):
                if skill:
                    unique_skills.add(skill)
        
        skills_list = list(unique_skills)
        
        if end_index is None:
            end_index = min(start_index + chunk_size, len(skills_list))
        else:
            end_index = min(end_index, len(skills_list))
        
        # Process only the specified chunk
        logger.info(f"Processing skills {start_index} to {end_index} of {len(skills_list)}")
        
        skills_to_process = skills_list[start_index:end_index]
        skill_count = 0
        
        # Process in very small batches
        batch_size = 5
        for i in range(0, len(skills_to_process), batch_size):
            batch = skills_to_process[i:i+batch_size]
            
            for skill_name in batch:
                # Truncate skill name to fit in database column (max 64 chars)
                if len(skill_name) > 60:
                    truncated_name = skill_name[:60] + "..."
                    skill_name_db = truncated_name
                else:
                    skill_name_db = skill_name
                
                # Check if skill already exists
                existing_skill = Skill.query.filter_by(name=skill_name_db).first()
                if not existing_skill:
                    skill = Skill(name=skill_name_db, category="From Kaggle Dataset")
                    db.session.add(skill)
                    skill_count += 1
            
            # Commit this batch
            db.session.commit()
            logger.info(f"Imported batch of {len(batch)} skills")
            
            # Pause between batches
            time.sleep(0.3)
        
        logger.info(f"Successfully imported {skill_count} skills from chunk")
        return True
    
    except Exception as e:
        logger.error(f"Error importing skills chunk: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    logger.info("Starting skills import step...")
    
    with app.app_context():
        # Use chunked import to avoid timeouts
        chunk_size = 50
        
        # If a specific range is provided as arguments, process just that range
        import sys
        if len(sys.argv) > 1:
            start_idx = int(sys.argv[1])
            end_idx = int(sys.argv[2]) if len(sys.argv) > 2 else None
            
            if import_skills_chunk(start_idx, end_idx):
                logger.info(f"Skills chunk {start_idx} to {end_idx or 'end'} successfully imported")
            else:
                logger.error(f"Failed to import skills chunk {start_idx} to {end_idx or 'end'}")
        else:
            # Otherwise, try to import all skills
            if import_skills():
                logger.info("All skills successfully imported")
            else:
                logger.error("Failed to import all skills")