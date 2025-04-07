import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import string
import os
import pickle
import nltk

# Configure logging
logger = logging.getLogger(__name__)

class CareerRecommendationEngine:
    def __init__(self):
        self.vectorizer = None
        self.career_vectors = None
        self.careers = None
        
        # Try to download NLTK data, but handle failures gracefully
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            self.stopwords = set(nltk.corpus.stopwords.words('english'))
            self.use_nltk = True
        except Exception as e:
            logger.warning(f"Failed to download NLTK resources: {e}. Using simple tokenization instead.")
            self.stopwords = set(['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
                                 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
                                 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
                                 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
                                 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
                                 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
                                 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
                                 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down',
                                 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here',
                                 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
                                 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
                                 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'])
            self.use_nltk = False

    def preprocess_text(self, text):
        """Preprocess text by removing punctuation, numbers, and stopwords."""
        if not text:
            return ""
            
        # Convert to lowercase and remove punctuation
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        
        # Remove numbers
        text = re.sub(r'\d+', '', text)
        
        # Tokenize the text
        if self.use_nltk:
            try:
                tokens = nltk.word_tokenize(text)
            except Exception as e:
                logger.warning(f"NLTK tokenization failed: {e}. Using simple split.")
                tokens = text.split()
        else:
            tokens = text.split()
            
        # Remove stopwords
        tokens = [word for word in tokens if word not in self.stopwords]
        
        return ' '.join(tokens)

    def create_career_vectors(self, careers):
        """
        Create TF-IDF vectors for careers
        
        Args:
            careers: List of career objects with title, description, and skills
        """
        logger.info(f"Creating career vectors for {len(careers)} careers")
        self.careers = careers
        
        # Create text representations for each career
        career_texts = []
        for career in careers:
            # Combine title, description, and skills into a single text
            skill_text = ' '.join([skill.name + ' ' + (skill.description or '') for skill in career.skills])
            career_text = f"{career.title} {career.description or ''} {skill_text}"
            career_texts.append(self.preprocess_text(career_text))
        
        # Create and fit TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(max_features=5000)
        self.career_vectors = self.vectorizer.fit_transform(career_texts)
        logger.info("Career vectors created successfully")

    def create_user_vector(self, user_data):
        """
        Create a TF-IDF vector from user assessment data
        
        Args:
            user_data: Dictionary containing user skills, interests, etc.
        """
        logger.info("Creating user vector")
        if not self.vectorizer:
            raise ValueError("Career vectors must be created before user vectors")
        
        # Combine all user data into a single text
        user_text = ""
        if 'skills' in user_data and user_data['skills']:
            skills_text = ' '.join([skill.name + ' ' + (skill.description or '') for skill in user_data['skills']])
            user_text += skills_text + " "
        
        if 'interests' in user_data and user_data['interests']:
            user_text += user_data['interests'] + " "
            
        if 'strengths' in user_data and user_data['strengths']:
            user_text += user_data['strengths'] + " "
            
        if 'personality_traits' in user_data and user_data['personality_traits']:
            user_text += user_data['personality_traits'] + " "
            
        # Add education and preferences
        if 'education_level' in user_data and user_data['education_level']:
            user_text += user_data['education_level'] + " "
            
        if 'preferences' in user_data and user_data['preferences']:
            pref = user_data['preferences']
            if hasattr(pref, 'salary_preference') and pref.salary_preference:
                user_text += f"salary {pref.salary_preference} "
            if hasattr(pref, 'location_preference') and pref.location_preference:
                user_text += f"location {pref.location_preference} "
                
        preprocessed_text = self.preprocess_text(user_text)
        logger.debug(f"Preprocessed user text: {preprocessed_text[:100]}...")
        
        # Transform using the existing vectorizer
        return self.vectorizer.transform([preprocessed_text])

    def get_career_recommendations(self, user_data, top_n=5):
        """
        Get career recommendations for a user
        
        Args:
            user_data: Dictionary containing user skills, interests, etc.
            top_n: Number of recommendations to return
            
        Returns:
            List of (career, score, reasoning) tuples
        """
        logger.info(f"Getting top {top_n} career recommendations")
        if not self.careers or not self.career_vectors or not self.vectorizer:
            raise ValueError("Career data not initialized. Run create_career_vectors first.")
            
        # Create user vector
        user_vector = self.create_user_vector(user_data)
        
        # Calculate similarity scores
        similarity_scores = cosine_similarity(user_vector, self.career_vectors).flatten()
        
        # Get top N recommendations
        top_indices = similarity_scores.argsort()[-top_n:][::-1]
        
        recommendations = []
        for idx in top_indices:
            career = self.careers[idx]
            score = similarity_scores[idx]
            
            # Generate reasoning
            reasoning = self.generate_recommendation_reasoning(career, user_data, score)
            
            recommendations.append((career, float(score), reasoning))
            
        return recommendations

    def generate_recommendation_reasoning(self, career, user_data, score):
        """Generate an explanation for why a career was recommended."""
        reasoning = f"This career matches your profile with a {score:.2f} similarity score. "
        
        # Add reasoning based on skills match
        if 'skills' in user_data and user_data['skills']:
            user_skill_names = {skill.name.lower() for skill in user_data['skills']}
            career_skill_names = {skill.name.lower() for skill in career.skills}
            matching_skills = user_skill_names.intersection(career_skill_names)
            
            if matching_skills:
                reasoning += f"You have {len(matching_skills)} relevant skills for this role: {', '.join(list(matching_skills)[:3])}. "
                
        # Add reasoning based on education match
        if 'education_level' in user_data and user_data['education_level'] and career.education_required:
            if user_data['education_level'].lower() in career.education_required.lower():
                reasoning += f"Your education level ({user_data['education_level']}) matches the requirements. "
                
        # Add reasoning based on salary preferences
        if 'preferences' in user_data and user_data['preferences']:
            pref = user_data['preferences']
            if hasattr(pref, 'salary_preference') and pref.salary_preference and career.avg_salary:
                try:
                    min_salary, max_salary = map(float, pref.salary_preference.split('-'))
                    if min_salary <= career.avg_salary <= max_salary:
                        reasoning += f"The average salary (${career.avg_salary:,.2f}) is within your preferred range. "
                except (ValueError, AttributeError):
                    pass
                    
        # Add growth rate information
        if career.growth_rate:
            reasoning += f"This career has a {career.growth_rate:.1f}% annual growth rate. "
            
        return reasoning

    def analyze_career_market_trends(self, career_id):
        """
        Analyze market trends for a specific career
        
        Args:
            career_id: ID of the career to analyze
            
        Returns:
            Dictionary with trend analysis
        """
        from models import MarketTrend, Career
        
        # Find the career
        career = Career.query.get(career_id)
        if not career:
            return {"error": "Career not found"}
            
        # Get market trends for this career
        trends = MarketTrend.query.filter_by(career_id=career_id).order_by(MarketTrend.year).all()
        if not trends:
            return {"error": "No market trend data available for this career"}
            
        # Extract trend data
        years = [trend.year for trend in trends]
        demand_levels = [trend.demand_level for trend in trends]
        salary_trends = [trend.salary_trend for trend in trends]
        job_counts = [trend.job_posting_count for trend in trends]
        
        # Calculate growth metrics
        avg_demand_growth = np.mean(np.diff(demand_levels)) if len(demand_levels) > 1 else 0
        avg_salary_growth = np.mean(salary_trends) if salary_trends else 0
        total_job_growth = (job_counts[-1] - job_counts[0]) / job_counts[0] if len(job_counts) > 1 and job_counts[0] > 0 else 0
        
        # Prepare the analysis
        analysis = {
            "career": career.title,
            "years_analyzed": years,
            "demand_levels": demand_levels,
            "salary_trends": salary_trends,
            "job_posting_counts": job_counts,
            "avg_demand_growth": float(avg_demand_growth),
            "avg_salary_growth": float(avg_salary_growth),
            "total_job_growth": float(total_job_growth),
            "outlook": self._generate_outlook_summary(avg_demand_growth, avg_salary_growth, total_job_growth)
        }
        
        return analysis
        
    def _generate_outlook_summary(self, demand_growth, salary_growth, job_growth):
        """Generate a human-readable outlook summary based on trend data."""
        outlook = ""
        
        # Demand growth assessment
        if demand_growth > 0.1:
            outlook += "Demand for this career is growing rapidly. "
        elif demand_growth > 0:
            outlook += "Demand for this career is showing steady growth. "
        elif demand_growth > -0.05:
            outlook += "Demand for this career is relatively stable. "
        else:
            outlook += "Demand for this career is declining. "
            
        # Salary growth assessment
        if salary_growth > 0.05:
            outlook += "Salaries are increasing at an above-average rate. "
        elif salary_growth > 0.02:
            outlook += "Salaries are growing steadily. "
        elif salary_growth > 0:
            outlook += "Salaries are increasing slightly. "
        else:
            outlook += "Salaries are stagnant or declining. "
            
        # Job growth assessment
        if job_growth > 0.2:
            outlook += "The number of job postings has increased significantly. "
        elif job_growth > 0:
            outlook += "The number of job postings has increased moderately. "
        elif job_growth > -0.1:
            outlook += "The number of job postings has remained relatively stable. "
        else:
            outlook += "The number of job postings has decreased. "
            
        # Overall assessment
        if demand_growth > 0 and salary_growth > 0 and job_growth > 0:
            outlook += "Overall, this career shows strong growth potential."
        elif demand_growth > 0 or salary_growth > 0 or job_growth > 0:
            outlook += "Overall, this career shows moderate growth potential."
        else:
            outlook += "Overall, this career may face challenges in the future."
            
        return outlook

    def save_model(self, filepath='career_recommendation_model.pkl'):
        """Save the model to a file."""
        if not self.vectorizer or not self.career_vectors.any():
            raise ValueError("Model not initialized")
            
        model_data = {
            'vectorizer': self.vectorizer,
            'career_vectors': self.career_vectors,
            'career_ids': [career.id for career in self.careers]
        }
        
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            logger.info(f"Model saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False
            
    def load_model(self, filepath='career_recommendation_model.pkl'):
        """Load the model from a file."""
        from models import Career
        
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
                
            self.vectorizer = model_data['vectorizer']
            self.career_vectors = model_data['career_vectors']
            
            # Load careers by IDs
            career_ids = model_data['career_ids']
            self.careers = [Career.query.get(id) for id in career_ids]
            
            logger.info(f"Model loaded from {filepath}")
            return True
        except FileNotFoundError:
            logger.warning(f"Model file {filepath} not found")
            return False
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False