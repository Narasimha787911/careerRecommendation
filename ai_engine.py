import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import string
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class CareerRecommendationEngine:
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
            text = re.sub(f'[{string.punctuation}]', ' ', text)
            
            # Remove numbers
            text = re.sub(r'\d+', '', text)
            
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text
        except Exception as e:
            logger.error(f"Error preprocessing text: {e}")
            return text or ""
    
    def create_career_vectors(self, careers):
        """
        Create TF-IDF vectors for careers
        
        Args:
            careers: List of career objects with title, description, and skills
        """
        self.careers = careers
        
        # Prepare document corpus for each career
        career_documents = []
        self.career_titles = []
        
        for career in careers:
            # Combine title, description, and skills
            skill_text = ' '.join([skill.name + ' ' + (skill.description or '') for skill in career.skills])
            
            document = f"{career.title} {career.description or ''} {skill_text} {career.education_required or ''} {career.work_environment or ''}"
            document = self.preprocess_text(document)
            
            career_documents.append(document)
            self.career_titles.append(career.title)
        
        try:
            # Create TF-IDF vectors
            self.career_vectors = self.vectorizer.fit_transform(career_documents)
            logger.info(f"Created TF-IDF vectors for {len(careers)} careers")
        except Exception as e:
            logger.error(f"Error creating career vectors: {e}")
            # Initialize with empty vectors as fallback
            self.career_vectors = np.zeros((len(careers), 1))
    
    def create_user_vector(self, user_data):
        """
        Create a TF-IDF vector from user assessment data
        
        Args:
            user_data: Dictionary containing user skills, interests, etc.
        """
        if not self.vectorizer or not self.career_vectors:
            logger.error("Vectorizer not initialized. Please call create_career_vectors first.")
            return None
        
        try:
            # Combine user data into a single document
            skills_text = ' '.join([skill.name + ' ' + (skill.description or '') for skill in user_data.get('skills', [])])
            interests = user_data.get('interests', '')
            strengths = user_data.get('strengths', '')
            personality = user_data.get('personality_traits', '')
            education = user_data.get('education_level', '')
            
            user_document = f"{skills_text} {interests} {strengths} {personality} {education}"
            user_document = self.preprocess_text(user_document)
            
            # Transform using the vectorizer fit on career data
            user_vector = self.vectorizer.transform([user_document])
            return user_vector
        
        except Exception as e:
            logger.error(f"Error creating user vector: {e}")
            # Return a zero vector as fallback
            return np.zeros((1, self.career_vectors.shape[1]))
    
    def get_career_recommendations(self, user_data, top_n=5):
        """
        Get career recommendations for a user
        
        Args:
            user_data: Dictionary containing user skills, interests, etc.
            top_n: Number of recommendations to return
            
        Returns:
            List of (career, score, reasoning) tuples
        """
        if not self.careers or self.career_vectors is None:
            logger.error("Career vectors not initialized. Please call create_career_vectors first.")
            return []
        
        try:
            # Create user vector
            user_vector = self.create_user_vector(user_data)
            
            if user_vector is None:
                logger.error("Failed to create user vector")
                return []
            
            # Calculate cosine similarity between user and careers
            similarities = cosine_similarity(user_vector, self.career_vectors).flatten()
            
            # Get top N career indices
            top_indices = similarities.argsort()[-top_n:][::-1]
            
            # Create recommendation list
            recommendations = []
            for idx in top_indices:
                career = self.careers[idx]
                score = similarities[idx]
                
                # Generate reasoning
                reasoning = self.generate_recommendation_reasoning(career, user_data, score)
                
                recommendations.append((career, float(score), reasoning))
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error getting career recommendations: {e}")
            return []
    
    def generate_recommendation_reasoning(self, career, user_data, score):
        """Generate an explanation for why a career was recommended."""
        try:
            # Get user skills that match career skills
            user_skills = set([skill.name.lower() for skill in user_data.get('skills', [])])
            career_skills = set([skill.name.lower() for skill in career.skills])
            
            matching_skills = user_skills.intersection(career_skills)
            
            # Get user education level compatibility
            education_match = "compatible"
            user_education = user_data.get('education_level', '').lower()
            career_education = (career.education_required or '').lower()
            
            if user_education and career_education:
                if 'bachelor' in user_education and ('master' in career_education or 'phd' in career_education):
                    education_match = "may need further education"
                elif 'high school' in user_education and 'bachelor' in career_education:
                    education_match = "may need further education"
            
            # Check interests alignment
            interests_alignment = "moderate"
            user_interests = (user_data.get('interests', '') or '').lower()
            
            if user_interests:
                career_keywords = self.preprocess_text(career.title + ' ' + (career.description or '')).split()
                interest_keywords = self.preprocess_text(user_interests).split()
                
                overlap = sum(1 for kw in interest_keywords if any(kw in ckw for ckw in career_keywords))
                
                if overlap > 3:
                    interests_alignment = "strong"
                elif overlap <= 1:
                    interests_alignment = "limited"
            
            # Build reasoning
            reasoning = f"This career has a {score:.0%} match with your profile."
            
            if matching_skills:
                skills_text = ", ".join(list(matching_skills)[:3])
                if len(matching_skills) > 3:
                    skills_text += f", and {len(matching_skills) - 3} more"
                reasoning += f" You already have key skills needed: {skills_text}."
            
            reasoning += f" Your education level is {education_match} with the requirements."
            
            if interests_alignment == "strong":
                reasoning += " Your interests strongly align with this career field."
            elif interests_alignment == "moderate":
                reasoning += " Your interests seem to align with aspects of this field."
            else:
                reasoning += " This field may expose you to new areas beyond your current interests."
            
            # Add career growth information
            if career.growth_rate:
                reasoning += f" This career has a {career.growth_rate:.1f}% annual growth rate,"
                if career.growth_rate > 10:
                    reasoning += " which is excellent."
                elif career.growth_rate > 5:
                    reasoning += " which is good."
                else:
                    reasoning += " which is steady."
            
            # Add salary information
            if career.avg_salary:
                reasoning += f" The average salary is ${career.avg_salary:,.0f} per year."
            
            return reasoning
            
        except Exception as e:
            logger.error(f"Error generating recommendation reasoning: {e}")
            return f"This career has a {score:.0%} match with your profile based on your skills, interests, and preferences."
    
    def analyze_career_market_trends(self, career_id):
        """
        Analyze market trends for a specific career
        
        Args:
            career_id: ID of the career to analyze
            
        Returns:
            Dictionary with trend analysis
        """
        from models import MarketTrend
        
        try:
            # Get trend data for this career
            trends = MarketTrend.query.filter_by(career_id=career_id).order_by(MarketTrend.year).all()
            
            if not trends or len(trends) < 2:
                return {
                    "error": "Insufficient trend data available for analysis",
                    "years_analyzed": 0
                }
            
            # Extract data points
            years = [trend.year for trend in trends]
            demand_levels = [trend.demand_level for trend in trends]
            salary_trends = [trend.salary_trend for trend in trends]
            job_counts = [trend.job_posting_count for trend in trends]
            
            # Calculate demand growth (simple linear regression)
            n = len(years)
            demand_slope = (n * sum(x*y for x, y in zip(years, demand_levels)) - sum(years) * sum(demand_levels)) / (n * sum(x*x for x in years) - sum(years)**2)
            
            # Calculate salary growth (use average of percentage changes)
            salary_growth = sum(salary_trends) / len(salary_trends) if salary_trends else 0
            
            # Calculate job posting growth (CAGR - Compound Annual Growth Rate)
            if job_counts and job_counts[0] > 0 and job_counts[-1] > 0:
                years_diff = years[-1] - years[0]
                job_growth = (job_counts[-1] / job_counts[0]) ** (1 / years_diff) - 1 if years_diff > 0 else 0
            else:
                job_growth = 0
            
            # Generate outlook summary
            outlook_summary = self._generate_outlook_summary(demand_slope, salary_growth, job_growth)
            
            # Return the analysis
            return {
                "years_analyzed": len(years),
                "years": years,
                "demand_levels": demand_levels,
                "salary_trends": salary_trends,
                "job_posting_counts": job_counts,
                "demand_growth": demand_slope,
                "salary_growth": salary_growth,
                "job_posting_growth": job_growth,
                "outlook_summary": outlook_summary
            }
        
        except Exception as e:
            logger.error(f"Error analyzing market trends: {e}")
            return {
                "error": f"Error analyzing market trends: {str(e)}",
                "years_analyzed": 0
            }
    
    def _generate_outlook_summary(self, demand_growth, salary_growth, job_growth):
        """Generate a human-readable outlook summary based on trend data."""
        # Determine overall outlook
        if demand_growth > 0.03 and salary_growth > 0.03 and job_growth > 0.05:
            outlook = "excellent"
        elif demand_growth > 0.01 and salary_growth > 0.02 and job_growth > 0.03:
            outlook = "very good"
        elif demand_growth > 0 and salary_growth > 0 and job_growth > 0:
            outlook = "good"
        elif demand_growth < -0.02 and salary_growth < 0 and job_growth < -0.03:
            outlook = "concerning"
        else:
            outlook = "stable"
        
        # Generate the summary text
        summary = f"The overall career outlook is {outlook}. "
        
        # Add demand growth description
        if demand_growth > 0.05:
            summary += "Demand for professionals in this field is growing rapidly. "
        elif demand_growth > 0.02:
            summary += "Demand for professionals in this field is growing steadily. "
        elif demand_growth > 0:
            summary += "Demand for professionals in this field is increasing slightly. "
        elif demand_growth < -0.02:
            summary += "Demand for professionals in this field is declining. "
        else:
            summary += "Demand for professionals in this field is relatively stable. "
        
        # Add salary growth description
        if salary_growth > 0.04:
            summary += "Salaries are increasing at an above-average rate. "
        elif salary_growth > 0.02:
            summary += "Salaries are growing at around the average inflation rate. "
        elif salary_growth > 0:
            summary += "Salaries are increasing slightly. "
        elif salary_growth < 0:
            summary += "Salaries have seen slight decreases. "
        else:
            summary += "Salaries have remained stable. "
        
        # Add job posting growth description
        if job_growth > 0.1:
            summary += "The number of job postings has increased significantly, indicating strong market demand."
        elif job_growth > 0.05:
            summary += "The number of job postings has increased steadily, suggesting good employment opportunities."
        elif job_growth > 0:
            summary += "The number of job postings has seen modest growth."
        elif job_growth < -0.05:
            summary += "The number of job postings has decreased, which may indicate a more competitive job market."
        else:
            summary += "The number of job postings has remained relatively constant."
        
        return summary
    
    def save_model(self, filepath='career_recommendation_model.pkl'):
        """Save the model to a file."""
        try:
            model_data = {
                'vectorizer': self.vectorizer,
                'career_vectors': self.career_vectors,
                'career_titles': self.career_titles
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
                
            logger.info(f"Model saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False
    
    def load_model(self, filepath='career_recommendation_model.pkl'):
        """Load the model from a file."""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
                
            self.vectorizer = model_data['vectorizer']
            self.career_vectors = model_data['career_vectors']
            self.career_titles = model_data['career_titles']
            
            logger.info(f"Model loaded from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False