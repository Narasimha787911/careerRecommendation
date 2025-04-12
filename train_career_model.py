import os
import pandas as pd
import numpy as np
import logging
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from kaggle_dataset_download import download_career_dataset
from models import Career, Skill, db
from ai_engine import CareerRecommendationEngine
from app import app

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_and_preprocess_data():
    """
    Load and preprocess the career recommendation dataset
    """
    try:
        # Check if dataset exists, download if not
        if not os.path.exists('data') or len(os.listdir('data')) == 0:
            success = download_career_dataset()
            if not success:
                logger.error("Failed to download dataset")
                return None
        
        # Load the dataset
        career_df = pd.read_csv('data/career_recommendation_data.csv')
        logger.info(f"Loaded dataset with {len(career_df)} rows")
        
        # Data exploration
        logger.info(f"Dataset columns: {career_df.columns.tolist()}")
        logger.info(f"Sample data:\n{career_df.head()}")
        
        # Return preprocessed data
        return career_df
    
    except Exception as e:
        logger.error(f"Error loading and preprocessing data: {e}")
        return None

def train_recommendation_model(career_data):
    """
    Train the career recommendation model using the dataset
    """
    try:
        engine = CareerRecommendationEngine()
        
        # Extract relevant features for vectorization
        # Modify this according to your dataset structure
        careers_for_vectorization = []
        
        for _, row in career_data.iterrows():
            career_dict = {
                'title': row['Title'],
                'description': row['Description'] if 'Description' in row else '',
                'skills': row['Skills'] if 'Skills' in row else '',
                'interests': row['Interests'] if 'Interests' in row else '',
                'requirements': row['Requirements'] if 'Requirements' in row else '',
            }
            careers_for_vectorization.append(career_dict)
        
        # Create career vectors
        engine.create_career_vectors(careers_for_vectorization)
        logger.info("Successfully created career vectors")
        
        # Save the trained model
        engine.save_model('data/trained_career_model.pkl')
        logger.info("Model trained and saved successfully")
        
        return engine
    
    except Exception as e:
        logger.error(f"Error training model: {e}")
        return None

def import_careers_to_database(career_data):
    """
    Import career data to the database
    """
    try:
        with app.app_context():
            # Clear existing careers and skills
            logger.info("Clearing existing career and skill data...")
            Career.query.delete()
            Skill.query.delete()
            db.session.commit()
            
            # Create skill dictionary
            unique_skills = set()
            skill_dict = {}
            
            for _, row in career_data.iterrows():
                if 'Skills' in row and isinstance(row['Skills'], str):
                    skills = [s.strip() for s in row['Skills'].split(',')]
                    for skill in skills:
                        if skill and skill not in unique_skills:
                            unique_skills.add(skill)
            
            # Add skills to database
            logger.info(f"Adding {len(unique_skills)} skills to database...")
            for skill_name in unique_skills:
                skill = Skill(name=skill_name, category="From Dataset")
                db.session.add(skill)
                db.session.flush()  # To get the generated ID
                skill_dict[skill_name] = skill
            
            # Add careers to database
            logger.info(f"Adding {len(career_data)} careers to database...")
            for _, row in career_data.iterrows():
                # Create career
                career = Career(
                    title=row['Title'],
                    description=row['Description'] if 'Description' in row else '',
                    education_required=row['Education'] if 'Education' in row else '',
                    avg_salary=float(row['Salary'].replace(',', '')) if 'Salary' in row and row['Salary'] else 0.0,
                    growth_rate=float(row['Growth Rate'].replace('%', '')) if 'Growth Rate' in row and row['Growth Rate'] else 0.0,
                    work_environment=row['Work Environment'] if 'Work Environment' in row else ''
                )
                
                db.session.add(career)
                
                # Add skills to career
                if 'Skills' in row and isinstance(row['Skills'], str):
                    skills = [s.strip() for s in row['Skills'].split(',')]
                    for skill_name in skills:
                        if skill_name and skill_name in skill_dict:
                            career.skills.append(skill_dict[skill_name])
            
            db.session.commit()
            logger.info("Successfully imported career data to database")
            return True
    
    except Exception as e:
        logger.error(f"Error importing data to database: {e}")
        db.session.rollback()
        return False

def main():
    """
    Main function to train the career recommendation model
    """
    logger.info("Starting career model training process...")
    
    # Load and preprocess data
    career_data = load_and_preprocess_data()
    if career_data is None:
        logger.error("Failed to load data. Exiting...")
        return
    
    # Train recommendation model
    model = train_recommendation_model(career_data)
    if model is None:
        logger.error("Failed to train model. Exiting...")
        return
    
    # Import careers to database
    success = import_careers_to_database(career_data)
    if not success:
        logger.error("Failed to import data to database. Exiting...")
        return
    
    logger.info("Career model training completed successfully!")

if __name__ == "__main__":
    main()