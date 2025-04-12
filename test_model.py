import os
import logging
import pickle
from models import User, Skill, Career, MarketTrend, db
from ai_engine import CareerRecommendationEngine
from app import app

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_trained_model():
    """Load the trained career recommendation model"""
    try:
        model_path = 'models/career_recommendation_model.pkl'
        if not os.path.exists(model_path):
            logger.error(f"Model file not found: {model_path}")
            return None
        
        engine = CareerRecommendationEngine()
        success = engine.load_model(model_path)
        
        if success:
            logger.info("Successfully loaded trained model")
            return engine
        else:
            logger.error("Failed to load model")
            return None
            
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return None

def get_sample_user_data():
    """Create sample user data for testing the model"""
    sample_users = [
        {
            'name': 'Software Developer Test',
            'skills': ['Python', 'SQL', 'Java', 'Problem Solving skills'],
            'interests': 'Technology, Software development, Data structures',
            'education_level': 'bachelor in computer science',
            'strengths': 'Analytical thinking, Critical thinking',
            'personality_traits': 'Detail-oriented, Logical'
        },
        {
            'name': 'Data Analyst Test',
            'skills': ['Python', 'SQL', 'Data Visualization skills( Power Bi/ Tableau )', 'Excel'],
            'interests': 'Data analytics, Research, Financial Analysis',
            'education_level': 'bachelor in statistics',
            'strengths': 'Analytical skills, Mathematics',
            'personality_traits': 'Detail-oriented, Organized'
        },
        {
            'name': 'Marketing Professional Test',
            'skills': ['Communication skills', 'Leadership', 'Sales', 'Social Media Marketing'],
            'interests': 'Sales/Marketing, Digital marketing, Market research',
            'education_level': 'bachelor in marketing',
            'strengths': 'Creativity, Communication',
            'personality_traits': 'Outgoing, Persuasive'
        }
    ]
    
    return sample_users

def test_recommendation_engine():
    """Test the recommendation engine with sample user data"""
    try:
        # Load the trained model
        engine = load_trained_model()
        if not engine:
            logger.error("Recommendation engine not available")
            return False
        
        # Load career data from database
        with app.app_context():
            careers = Career.query.all()
            engine.careers = careers
            
            # Get sample user data
            sample_users = get_sample_user_data()
            
            # Generate recommendations for each sample user
            for user_data in sample_users:
                logger.info(f"\nGenerating recommendations for: {user_data['name']}")
                logger.info(f"Skills: {user_data['skills']}")
                logger.info(f"Interests: {user_data['interests']}")
                
                recommendations = engine.get_career_recommendations(user_data, top_n=3)
                
                if recommendations:
                    logger.info("Top 3 Career Recommendations:")
                    
                    for i, (career, score, reasoning) in enumerate(recommendations, 1):
                        logger.info(f"{i}. {career.title} (Match: {score:.1%})")
                        logger.info(f"   {reasoning}\n")
                else:
                    logger.info("No recommendations found for this user profile")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing recommendation engine: {e}")
        return False

def main():
    """Main function to test the career recommendation model"""
    logger.info("Starting career recommendation model testing...")
    
    success = test_recommendation_engine()
    
    if success:
        logger.info("Career recommendation model testing completed successfully!")
    else:
        logger.error("Career recommendation model testing failed!")

if __name__ == "__main__":
    main()