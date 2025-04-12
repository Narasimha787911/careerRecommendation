import os
import pandas as pd
import numpy as np
import re
import logging
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from models import Career, Skill, MarketTrend, db
from ai_engine import CareerRecommendationEngine
from app import app

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_text(text):
    """Clean text by removing special characters and extra spaces"""
    if not isinstance(text, str):
        return ""
    # Remove special characters
    text = re.sub(r'[^\w\s]', ' ', text)
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_career_info(row):
    """Extract career information from a dataset row"""
    # Get course/degree as title
    title = row.get('What was your course in UG?', '')
    if row.get('What is your UG specialization? Major Subject (Eg; Mathematics)', ''):
        title += ' in ' + row.get('What is your UG specialization? Major Subject (Eg; Mathematics)', '')
    
    # Use interests as description
    description = row.get('What are your interests?', '')
    
    # Use skills as skill list
    skills_text = row.get('What are your skills ? (Select multiple if necessary)', '')
    
    # Get job title if available
    job_title = row.get('If yes, then what is/was your first Job title in your current field of work? If not applicable, write NA.               ', '')
    if job_title and job_title.lower() != 'na':
        job_description = f"This career path can lead to jobs such as {job_title}."
    else:
        job_description = ""
    
    # Combine additional information
    masters = row.get('Have you done masters after undergraduation? If yes, mention your field of masters.(Eg; Masters in Mathematics)', '')
    if masters and masters.lower() != 'no' and masters.strip():
        education = f"Advanced degree such as {masters} can be beneficial."
    else:
        education = "Bachelor's degree required."
    
    # Add certification information
    certification = row.get('Did you do any certification courses additionally?', '')
    cert_title = row.get('If yes, please specify your certificate course title.', '')
    
    if certification == 'Yes' and cert_title and cert_title.lower() != 'no':
        cert_info = f"Certifications such as {cert_title} can enhance career prospects."
    else:
        cert_info = "Professional certifications may be beneficial."
    
    # Full description
    full_description = f"{description} {job_description} {cert_info}"
    
    # Clean up text fields
    title = clean_text(title)
    description = clean_text(full_description)
    skills = [clean_text(s.strip()) for s in skills_text.split(';')] if isinstance(skills_text, str) else []
    
    # Set education required
    education_required = education
    
    # Extract salary information (placeholder - would need real data)
    avg_salary = np.random.normal(75000, 15000)  # Generate random salary for demonstration
    
    # Extract growth rate (placeholder - would need real data)
    growth_rate = np.random.normal(5, 2)  # Generate random growth rate for demonstration
    
    return {
        'title': title,
        'description': description,
        'skills': [s for s in skills if s],  # Filter out empty skills
        'education_required': education_required,
        'avg_salary': avg_salary,
        'growth_rate': growth_rate,
        'work_environment': 'Typical work settings include office environments, remote work opportunities, and field work depending on specialization.'
    }

def load_and_process_dataset():
    """Load and process the career recommendation dataset"""
    try:
        # Load the dataset
        file_path = 'data/career_recommender.csv'
        if not os.path.exists(file_path):
            logger.error(f"Dataset file not found: {file_path}")
            return []
        
        df = pd.read_csv(file_path)
        logger.info(f"Loaded dataset with {len(df)} rows")
        
        # Process each row to extract career information
        careers = []
        
        for _, row in df.iterrows():
            # Skip rows with minimal information
            if pd.isna(row.get('What was your course in UG?', '')) or pd.isna(row.get('What is your UG specialization? Major Subject (Eg; Mathematics)', '')):
                continue
                
            career_info = extract_career_info(row)
            careers.append(career_info)
        
        # Create a unique list of careers by title
        unique_careers = {}
        for career in careers:
            title = career['title'].lower()
            if title and title not in unique_careers:
                unique_careers[title] = career
        
        logger.info(f"Extracted {len(unique_careers)} unique careers from dataset")
        return list(unique_careers.values())
    
    except Exception as e:
        logger.error(f"Error loading and processing dataset: {e}")
        return []

def train_model(career_data):
    """Train the career recommendation model using the processed data"""
    try:
        # Initialize the recommendation engine
        engine = CareerRecommendationEngine()
        
        # Create career vectors
        engine.create_career_vectors(career_data)
        logger.info("Successfully created career vectors")
        
        # Save the trained model
        os.makedirs('models', exist_ok=True)
        engine.save_model('models/career_recommendation_model.pkl')
        logger.info("Model trained and saved successfully")
        
        return engine
    
    except Exception as e:
        logger.error(f"Error training model: {e}")
        return None

def import_to_database(career_data):
    """Import career data to the database"""
    try:
        with app.app_context():
            # Create skill dictionary
            unique_skills = set()
            
            for career in career_data:
                for skill in career.get('skills', []):
                    if skill:
                        unique_skills.add(skill)
            
            # Clear existing careers and skills
            logger.info("Clearing existing career and skill data...")
            Career.query.delete()
            Skill.query.delete()
            MarketTrend.query.delete()
            db.session.commit()
            
            # Add skills to database
            skill_dict = {}
            logger.info(f"Adding {len(unique_skills)} skills to database...")
            
            for skill_name in unique_skills:
                skill = Skill(name=skill_name, category="From Dataset")
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
                        source="Career Survey Analysis"
                    )
                    db.session.add(trend)
            
            db.session.commit()
            logger.info("Successfully imported career data to database")
            return True
    
    except Exception as e:
        logger.error(f"Error importing data to database: {e}")
        db.session.rollback()
        return False

def main():
    """Main function to process dataset and train model"""
    logger.info("Starting career dataset processing and model training...")
    
    # Load and process dataset
    career_data = load_and_process_dataset()
    if not career_data:
        logger.error("Failed to process dataset. Exiting...")
        return
    
    # Train model
    model = train_model(career_data)
    if not model:
        logger.error("Failed to train model. Exiting...")
        return
    
    # Import to database
    success = import_to_database(career_data)
    if not success:
        logger.error("Failed to import data to database. Exiting...")
        return
    
    logger.info("Career dataset processing and model training completed successfully!")

if __name__ == "__main__":
    main()