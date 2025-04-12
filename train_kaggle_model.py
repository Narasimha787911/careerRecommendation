import os
import pandas as pd
import numpy as np
import re
import logging
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CareerData:
    """Simple class to hold career data for training"""
    def __init__(self, title, description, skills, education_required, avg_salary, growth_rate, work_environment):
        self.title = title
        self.description = description
        self.skills = skills
        self.education_required = education_required
        self.avg_salary = avg_salary
        self.growth_rate = growth_rate
        self.work_environment = work_environment

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
    title = str(row.get('What was your course in UG?', ''))
    spec = str(row.get('What is your UG specialization? Major Subject (Eg; Mathematics)', ''))
    if spec and spec.lower() != 'nan':
        title += ' in ' + spec
    
    # Use interests as description
    interests = str(row.get('What are your interests?', ''))
    description = interests if interests.lower() != 'nan' else "Various field-related interests"
    
    # Use skills as skill list
    skills_text = str(row.get('What are your skills ? (Select multiple if necessary)', ''))
    if skills_text.lower() == 'nan':
        skills_text = ''
    
    # Get job title if available
    job_title = str(row.get('If yes, then what is/was your first Job title in your current field of work? If not applicable, write NA.               ', ''))
    if job_title and job_title.lower() not in ('na', 'nan'):
        job_description = f"This career path can lead to jobs such as {job_title}."
    else:
        job_description = ""
    
    # Combine additional information
    masters = str(row.get('Have you done masters after undergraduation? If yes, mention your field of masters.(Eg; Masters in Mathematics)', ''))
    if masters and masters.lower() not in ('no', 'nan') and masters.strip():
        education = f"Advanced degree such as {masters} can be beneficial."
    else:
        education = "Bachelor's degree required."
    
    # Add certification information
    certification = str(row.get('Did you do any certification courses additionally?', ''))
    cert_title = str(row.get('If yes, please specify your certificate course title.', ''))
    
    if certification == 'Yes' and cert_title and cert_title.lower() not in ('no', 'nan'):
        cert_info = f"Certifications such as {cert_title} can enhance career prospects."
    else:
        cert_info = "Professional certifications may be beneficial."
    
    # Full description
    full_description = f"{description} {job_description} {cert_info}"
    
    # Clean up text fields
    title = clean_text(title)
    description = clean_text(full_description)
    skills = [clean_text(s.strip()) for s in skills_text.split(';')] if skills_text else []
    
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
        
        # Read CSV file with appropriate handling of NaN values
        df = pd.read_csv(file_path)
        # Fill NaN values with empty strings to avoid errors
        df = df.fillna('')
        
        logger.info(f"Loaded dataset with {len(df)} rows")
        
        # Process each row to extract career information
        careers = []
        
        for _, row in df.iterrows():
            # Skip rows with minimal information
            course = row.get('What was your course in UG?', '')
            specialization = row.get('What is your UG specialization? Major Subject (Eg; Mathematics)', '')
            
            if not course or not specialization:
                continue
                
            try:
                career_info = extract_career_info(row)
                careers.append(career_info)
            except Exception as e:
                logger.warning(f"Error processing row: {e}")
                continue
        
        # Create a unique list of careers by title
        unique_careers = {}
        for career in careers:
            title = career['title'].lower()
            if title and title not in unique_careers:
                unique_careers[title] = career
        
        logger.info(f"Extracted {len(unique_careers)} unique careers from dataset")
        
        # Convert dictionary data to Career objects for the AI engine
        career_objects = []
        for career_dict in unique_careers.values():
            # Create a skill object for each skill
            skill_objects = []
            for skill_name in career_dict['skills']:
                class Skill:
                    def __init__(self, name):
                        self.name = name
                        self.description = ""
                
                skill_objects.append(Skill(skill_name))
            
            # Create a Career object
            career = CareerData(
                title=career_dict['title'],
                description=career_dict['description'],
                skills=skill_objects,
                education_required=career_dict['education_required'],
                avg_salary=career_dict['avg_salary'],
                growth_rate=career_dict['growth_rate'],
                work_environment=career_dict['work_environment']
            )
            
            career_objects.append(career)
        
        return career_objects
    
    except Exception as e:
        logger.error(f"Error loading and processing dataset: {e}, {type(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []

class KaggleCareerRecommendationEngine:
    """Simplified version of the career recommendation engine for training"""
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.careers = []
        self.career_vectors = None
        self.career_titles = []
    
    def preprocess_text(self, text):
        """Preprocess text by removing punctuation, numbers, and stopwords."""
        if not text:
            return ""
        
        try:
            # Convert to lowercase
            text = text.lower()
            
            # Remove punctuation
            text = re.sub(r'[^\w\s]', ' ', text)
            
            # Remove numbers
            text = re.sub(r'\d+', '', text)
            
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text
        except Exception as e:
            logger.error(f"Error preprocessing text: {e}")
            return text or ""
    
    def create_career_vectors(self, careers):
        """Create TF-IDF vectors for careers"""
        self.careers = careers
        
        # Prepare document corpus for each career
        career_documents = []
        self.career_titles = []
        
        for career in careers:
            # Combine title, description, and skills
            skill_text = ' '.join([skill.name for skill in career.skills])
            
            document = f"{career.title} {career.description} {skill_text} {career.education_required} {career.work_environment}"
            document = self.preprocess_text(document)
            
            career_documents.append(document)
            self.career_titles.append(career.title)
        
        try:
            # Create TF-IDF vectors
            self.career_vectors = self.vectorizer.fit_transform(career_documents)
            logger.info(f"Created TF-IDF vectors for {len(careers)} careers")
        except Exception as e:
            logger.error(f"Error creating career vectors: {e}")
            self.career_vectors = np.zeros((len(careers), 1))  # Fallback
    
    def save_model(self, filepath='career_recommendation_model.pkl'):
        """Save the model to a file."""
        try:
            model_data = {
                'vectorizer': self.vectorizer,
                'career_vectors': self.career_vectors,
                'career_titles': self.career_titles
            }
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
                
            logger.info(f"Model saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False

def generate_career_json(careers):
    """Generate JSON representation of careers for database import"""
    careers_json = []
    
    for career in careers:
        career_dict = {
            'title': career.title,
            'description': career.description,
            'skills': [skill.name for skill in career.skills],
            'education_required': career.education_required,
            'avg_salary': career.avg_salary,
            'growth_rate': career.growth_rate,
            'work_environment': career.work_environment
        }
        
        careers_json.append(career_dict)
    
    # Save the JSON for import
    import json
    
    os.makedirs('models', exist_ok=True)
    
    with open('models/careers.json', 'w') as f:
        json.dump(careers_json, f, indent=2)
    
    logger.info(f"Saved career data to models/careers.json for database import")

def main():
    """Main function to process dataset and train model"""
    logger.info("Starting Kaggle career dataset processing and model training...")
    
    # Load and process dataset
    career_data = load_and_process_dataset()
    if not career_data:
        logger.error("Failed to process dataset. Exiting...")
        return
    
    # Train model
    engine = KaggleCareerRecommendationEngine()
    engine.create_career_vectors(career_data)
    
    # Save the model
    os.makedirs('models', exist_ok=True)
    success = engine.save_model('models/career_recommendation_model.pkl')
    
    if not success:
        logger.error("Failed to save model. Exiting...")
        return
    
    # Generate career JSON for database import
    generate_career_json(career_data)
    
    logger.info("Kaggle career dataset processing and model training completed successfully!")

if __name__ == "__main__":
    main()