import os
import json
import pandas as pd
import logging
from ai_engine import CareerRecommendationEngine
from app import app, db
from sqlalchemy import text
from models import Career, Skill, MarketTrend

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_career_data():
    """Load career data from the generated dataset"""
    try:
        # Check if careers.json exists
        if not os.path.exists('data/careers.json'):
            logger.error("careers.json not found. Run download_career_dataset.py first.")
            return False
        
        # Check if market_trends.json exists
        if not os.path.exists('data/market_trends.json'):
            logger.error("market_trends.json not found. Run download_career_dataset.py first.")
            return False
        
        # Load careers from JSON file
        with open('data/careers.json', 'r') as f:
            careers_data = json.load(f)
        
        # Load market trends from JSON file
        with open('data/market_trends.json', 'r') as f:
            trends_data = json.load(f)
        
        logger.info(f"Loaded {len(careers_data)} careers and {len(trends_data)} market trends")
        return careers_data, trends_data
    
    except Exception as e:
        logger.error(f"Error loading career data: {e}")
        return None, None

def populate_database(careers_data, trends_data):
    """Populate the database with careers and market trends data"""
    try:
        with app.app_context():
            # Check existing data - check for any recommendations in the database
            existing_recommendations = db.session.execute(text("SELECT COUNT(*) FROM recommendation")).scalar()
            existing_careers = Career.query.count()
            
            if existing_recommendations > 0:
                logger.info(f"Found {existing_recommendations} existing recommendations. Will update careers instead of replacing them.")
                # Update existing careers instead of deleting them
                existing_career_ids = [career.id for career in Career.query.all()]
                
                # Create skills dictionary to store/retrieve skills
                skill_dict = {}
                
                # Process each career
                for career_item in careers_data:
                    career_id = career_item.get('Career_id')
                    
                    # Check if career exists
                    career = Career.query.get(career_id)
                    if not career:
                        # Create new career if it doesn't exist
                        career = Career(id=career_id)
                    
                    # Update career fields
                    career.title = career_item.get('Career_title')
                    career.description = career_item.get('Description')
                    career.avg_salary = float(career_item.get('Average_salary', '0').replace('$', '').replace(',', ''))
                    career.growth_rate = float(career_item.get('Job_outlook', '0%').split('%')[0])
                    career.education_required = career_item.get('Education_required')
                    career.work_environment = career_item.get('Work_environment')
                    career.job_outlook = career_item.get('Job_outlook')
                    
                    # Extract skills list from string
                    skills_list = career_item.get('Skills_required', '').split(', ')
                    
                    # Clear existing skills
                    career.skills = []
                    
                    # Add skills to career
                    for skill_name in skills_list:
                        skill_name = skill_name.strip()
                        if not skill_name:
                            continue
                        
                        # Check if skill already exists in dictionary
                        if skill_name not in skill_dict:
                            # Check if skill exists in database
                            skill = Skill.query.filter_by(name=skill_name).first()
                            if not skill:
                                # Create new skill
                                skill = Skill(name=skill_name, category="Technical")
                                db.session.add(skill)
                                db.session.flush()  # Get ID without committing
                            
                            skill_dict[skill_name] = skill
                        
                        # Add skill to career
                        career.skills.append(skill_dict[skill_name])
                    
                    # Add or update career
                    db.session.add(career)
                
                # Commit careers and skills
                db.session.commit()
                logger.info(f"Updated {len(careers_data)} careers in the database")
            else:
                # Safe to delete existing data since there are no recommendations
                logger.info("No existing recommendations found. Safe to delete existing careers.")
                
                # Clear existing data
                MarketTrend.query.delete()
                Career.query.delete()
                
                # Create skills dictionary to store/retrieve skills
                skill_dict = {}
                
                # Process each career
                for career_item in careers_data:
                    # Extract skills list from string
                    skills_list = career_item.get('Skills_required', '').split(', ')
                    
                    # Create career object
                    career = Career(
                        id=career_item.get('Career_id'),
                        title=career_item.get('Career_title'),
                        description=career_item.get('Description'),
                        avg_salary=float(career_item.get('Average_salary', '0').replace('$', '').replace(',', '')),
                        growth_rate=float(career_item.get('Job_outlook', '0%').split('%')[0]),
                        education_required=career_item.get('Education_required'),
                        work_environment=career_item.get('Work_environment'),
                        job_outlook=career_item.get('Job_outlook')
                    )
                    
                    # Add skills to career
                    for skill_name in skills_list:
                        skill_name = skill_name.strip()
                        if not skill_name:
                            continue
                        
                        # Check if skill already exists in dictionary
                        if skill_name not in skill_dict:
                            # Check if skill exists in database
                            skill = Skill.query.filter_by(name=skill_name).first()
                            if not skill:
                                # Create new skill
                                skill = Skill(name=skill_name, category="Technical")
                                db.session.add(skill)
                                db.session.flush()  # Get ID without committing
                            
                            skill_dict[skill_name] = skill
                        
                        # Add skill to career
                        career.skills.append(skill_dict[skill_name])
                    
                    # Add career to database
                    db.session.add(career)
                
                # Commit careers and skills
                db.session.commit()
                logger.info(f"Added {len(careers_data)} careers to the database")
            
            # Delete existing market trends and add new ones
            MarketTrend.query.delete()
            
            # Process market trends
            for trend_item in trends_data:
                trend = MarketTrend(
                    career_id=trend_item.get('Career_id'),
                    year=trend_item.get('Year'),
                    demand_level=trend_item.get('Demand_level'),
                    salary_trend=trend_item.get('Salary_trend'),
                    job_posting_count=trend_item.get('Job_posting_count'),
                    source=trend_item.get('Source'),
                    notes=trend_item.get('Notes')
                )
                db.session.add(trend)
            
            # Commit market trends
            db.session.commit()
            logger.info(f"Added {len(trends_data)} market trends to the database")
            
            return True
    
    except Exception as e:
        logger.error(f"Error populating database: {e}")
        db.session.rollback()
        return False

def train_recommendation_model():
    """Train the career recommendation model using data from the database"""
    try:
        with app.app_context():
            # Create recommendation engine
            engine = CareerRecommendationEngine()
            
            # Get all careers with their skills
            careers = Career.query.all()
            if not careers:
                logger.error("No careers found in the database")
                return False
            
            # Create career vectors
            engine.create_career_vectors(careers)
            
            # Save the trained model
            model_saved = engine.save_model('career_recommendation_model.pkl')
            
            if model_saved:
                logger.info("Career recommendation model trained and saved successfully")
                return True
            else:
                logger.error("Failed to save the trained model")
                return False
    
    except Exception as e:
        logger.error(f"Error training recommendation model: {e}")
        return False

def test_model():
    """Test the trained model with sample user data"""
    try:
        with app.app_context():
            # Create recommendation engine
            engine = CareerRecommendationEngine()
            
            # Load the trained model
            model_loaded = engine.load_model('career_recommendation_model.pkl')
            if not model_loaded:
                logger.error("Failed to load the trained model")
                return False
            
            # Get a few skills from the database
            skills = Skill.query.limit(5).all()
            
            # Create sample user data
            sample_user_data = {
                'interests': 'programming, technology, problem-solving, data analysis',
                'strengths': 'analytical thinking, attention to detail, creativity',
                'personality_traits': 'analytical, logical, detail-oriented',
                'education_level': 'bachelor degree in computer science',
                'skills': skills if skills else []
            }
            
            # Get recommendations
            recommendations = engine.get_career_recommendations(sample_user_data, top_n=5)
            
            logger.info("Top 5 career recommendations for sample user:")
            for career, score, reasoning in recommendations:
                logger.info(f"- {career.title} (Score: {score:.2f})")
                logger.info(f"  Reasoning: {reasoning}")
            
            return True
    
    except Exception as e:
        logger.error(f"Error testing model: {e}")
        return False

if __name__ == "__main__":
    # Load data from files
    careers_data, trends_data = load_career_data()
    if not careers_data or not trends_data:
        logger.error("Failed to load career data. Exiting.")
        exit(1)
    
    # Populate database
    success = populate_database(careers_data, trends_data)
    if not success:
        logger.error("Failed to populate database. Exiting.")
        exit(1)
    
    # Train model
    success = train_recommendation_model()
    if not success:
        logger.error("Failed to train model. Exiting.")
        exit(1)
    
    # Test model
    success = test_model()
    if not success:
        logger.error("Model testing failed. The model may not work correctly.")
    else:
        logger.info("Model training and testing completed successfully.")