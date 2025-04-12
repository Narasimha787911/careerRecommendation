import os
import json
import logging
import time
from datetime import datetime
from app import app, db
from models import Career, Skill
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_careers():
    """Import careers from career data"""
    try:
        # Load the processed career data
        careers_file = 'models/careers.json'
        if not os.path.exists(careers_file):
            logger.error(f"Career data file not found: {careers_file}")
            return False
        
        with open(careers_file, 'r') as f:
            career_data = json.load(f)
        
        logger.info(f"Loaded career data with {len(career_data)} careers")
        
        # Get all skills from the database
        skills = Skill.query.all()
        skill_dict = {skill.name: skill for skill in skills}
        
        # For truncated skill names, create a secondary lookup
        truncated_skill_dict = {}
        for skill_name in [s for s in skill_dict.keys() if s.endswith('...')]:
            original_prefix = skill_name[:-3]  # Remove the '...'
            truncated_skill_dict[original_prefix] = skill_dict[skill_name]
        
        logger.info(f"Loaded {len(skill_dict)} skills from database")
        
        # Import careers in batches
        career_count = 0
        batch_size = 10
        
        logger.info(f"Importing {len(career_data)} careers in batches of {batch_size}...")
        
        for i in range(0, len(career_data), batch_size):
            batch = career_data[i:i+batch_size]
            
            # Process this batch
            for career_info in batch:
                # Extract skills for this career
                career_skills = career_info.get('skills', [])
                skills_text = ", ".join(career_skills) if career_skills else "Not specified"
                
                # Create career with new schema
                career = Career(
                    name=career_info['title'],  # 'title' in JSON maps to 'name' in DB
                    description=career_info['description'],
                    required_skills=skills_text,
                    industry=career_info.get('industry', 'General'),
                    created_at=datetime.utcnow()
                )
                
                db.session.add(career)
                db.session.flush()  # Get the ID
                
                # Add skills to career
                added_skill_ids = set()  # Track skills that have been added to avoid duplicates
                
                for skill_name in career_skills:
                    # Try exact match first
                    if skill_name in skill_dict:
                        skill = skill_dict[skill_name]
                        if skill.id not in added_skill_ids:
                            career.skills.append(skill)
                            added_skill_ids.add(skill.id)
                    else:
                        # Try to find a matching truncated skill
                        found_skill = False
                        for prefix, skill in truncated_skill_dict.items():
                            if skill_name.startswith(prefix):
                                if skill.id not in added_skill_ids:
                                    career.skills.append(skill)
                                    added_skill_ids.add(skill.id)
                                found_skill = True
                                break
                        
                        if not found_skill:
                            # If still not found, look for a partial match in the regular skills
                            for db_skill_name, skill in skill_dict.items():
                                if skill_name in db_skill_name or db_skill_name in skill_name:
                                    if skill.id not in added_skill_ids:
                                        career.skills.append(skill)
                                        added_skill_ids.add(skill.id)
                                    break
                
                career_count += 1
            
            # Commit this batch
            db.session.commit()
            logger.info(f"Imported {min(i + batch_size, len(career_data))} of {len(career_data)} careers")
            
            # Brief pause to avoid overwhelming the database
            time.sleep(0.5)
        
        logger.info(f"Successfully imported {career_count} careers")
        return True
    
    except Exception as e:
        logger.error(f"Error importing careers: {e}")
        db.session.rollback()
        return False

def import_careers_chunk(start_index=0, end_index=None, chunk_size=20):
    """Import a specific chunk of careers"""
    try:
        # Load the processed career data
        careers_file = 'models/careers.json'
        if not os.path.exists(careers_file):
            logger.error(f"Career data file not found: {careers_file}")
            return False
        
        with open(careers_file, 'r') as f:
            career_data = json.load(f)
        
        # Determine the range to process
        if end_index is None:
            end_index = min(start_index + chunk_size, len(career_data))
        else:
            end_index = min(end_index, len(career_data))
        
        # Process only the specified chunk
        logger.info(f"Processing careers {start_index} to {end_index} of {len(career_data)}")
        careers_to_process = career_data[start_index:end_index]
        
        # Get all skills from the database
        skills = Skill.query.all()
        skill_dict = {skill.name: skill for skill in skills}
        
        # For truncated skill names, create a secondary lookup
        truncated_skill_dict = {}
        for skill_name in [s for s in skill_dict.keys() if s.endswith('...')]:
            original_prefix = skill_name[:-3]  # Remove the '...'
            truncated_skill_dict[original_prefix] = skill_dict[skill_name]
        
        logger.info(f"Loaded {len(skill_dict)} skills from database")
        
        # Process in small batches
        career_count = 0
        batch_size = 5
        for i in range(0, len(careers_to_process), batch_size):
            batch = careers_to_process[i:i+batch_size]
            
            # Process this batch
            for career_info in batch:
                # Extract skills for this career
                career_skills = career_info.get('skills', [])
                skills_text = ", ".join(career_skills) if career_skills else "Not specified"
                
                # Create career with new schema
                career = Career(
                    name=career_info['title'],  # 'title' in JSON maps to 'name' in DB
                    description=career_info['description'],
                    required_skills=skills_text,
                    industry=career_info.get('industry', 'General'),
                    created_at=datetime.utcnow()
                )
                
                db.session.add(career)
                db.session.flush()  # Get the ID
                
                # Add skills to career through the association table
                added_skill_ids = set()  # Track skills that have been added to avoid duplicates
                
                for skill_name in career_skills:
                    # Try exact match first
                    if skill_name in skill_dict:
                        skill = skill_dict[skill_name]
                        if skill.id not in added_skill_ids:
                            career.skills.append(skill)
                            added_skill_ids.add(skill.id)
                    else:
                        # Try to find a matching truncated skill
                        found_skill = False
                        for prefix, skill in truncated_skill_dict.items():
                            if skill_name.startswith(prefix):
                                if skill.id not in added_skill_ids:
                                    career.skills.append(skill)
                                    added_skill_ids.add(skill.id)
                                found_skill = True
                                break
                        
                        if not found_skill:
                            # If still not found, look for a partial match
                            for db_skill_name, skill in skill_dict.items():
                                if skill_name in db_skill_name or db_skill_name in skill_name:
                                    if skill.id not in added_skill_ids:
                                        career.skills.append(skill)
                                        added_skill_ids.add(skill.id)
                                    break
                
                career_count += 1
            
            # Commit this batch
            db.session.commit()
            logger.info(f"Imported batch of {len(batch)} careers")
            
            # Brief pause to avoid overwhelming the database
            time.sleep(0.3)
        
        logger.info(f"Successfully imported {career_count} careers from chunk")
        return True
    
    except Exception as e:
        logger.error(f"Error importing careers chunk: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    logger.info("Starting careers import step...")
    
    with app.app_context():
        # If a specific range is provided as arguments, process just that range
        import sys
        if len(sys.argv) > 1:
            start_idx = int(sys.argv[1])
            end_idx = int(sys.argv[2]) if len(sys.argv) > 2 else None
            
            if import_careers_chunk(start_idx, end_idx):
                logger.info(f"Careers chunk {start_idx} to {end_idx or 'end'} successfully imported")
            else:
                logger.error(f"Failed to import careers chunk {start_idx} to {end_idx or 'end'}")
        else:
            # Otherwise, try to import all careers
            if import_careers():
                logger.info("All careers successfully imported")
            else:
                logger.error("Failed to import all careers")