import numpy as np
import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
import logging

# Initialize logging
logger = logging.getLogger(__name__)

# Download NLTK resources if not already downloaded
try:
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('stopwords')
    nltk.download('wordnet')

class CareerRecommendationEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        # Try to load stopwords, fallback to empty set if it fails
        try:
            self.stop_words = set(stopwords.words('english'))
        except Exception as e:
            logger.warning(f"Could not load stopwords, using empty set instead: {e}")
            self.stop_words = set()
            
        # Initialize lemmatizer with error handling
        try:
            self.lemmatizer = WordNetLemmatizer()
        except Exception as e:
            logger.warning(f"Could not initialize lemmatizer: {e}")
            # Create a simple pass-through "lemmatizer"
            self.lemmatizer = type('DummyLemmatizer', (), {'lemmatize': lambda self, word: word})()
        
    def preprocess_text(self, text):
        """Preprocess text by tokenizing, removing stopwords, and lemmatizing."""
        if not text:
            return ""
            
        # Lowercase and remove special characters
        text = re.sub(r'[^\w\s]', '', text.lower())
        
        # Tokenize using simple split (avoid NLTK tokenizer issues)
        tokens = text.split()
        
        # Remove stopwords and lemmatize
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens if token not in self.stop_words]
        
        return ' '.join(tokens)
    
    def process_skills(self, skills_list):
        """Process a list of skills and return a preprocessed string."""
        if not skills_list:
            return ""
        return self.preprocess_text(' '.join(skills_list))
    
    def process_interests(self, interests_list):
        """Process a list of interests and return a preprocessed string."""
        if not interests_list:
            return ""
        return self.preprocess_text(' '.join(interests_list))
    
    def calculate_skill_match(self, user_skills, career_required_skills):
        """Calculate matching score between user skills and career required skills."""
        if not user_skills or not career_required_skills:
            return 0.0
            
        processed_user_skills = self.process_skills(user_skills)
        processed_career_skills = self.process_skills(career_required_skills)
        
        if not processed_user_skills or not processed_career_skills:
            return 0.0
            
        # Create a small corpus with just these two documents
        corpus = [processed_user_skills, processed_career_skills]
        
        try:
            # Transform the corpus to TF-IDF feature vectors
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating skill match: {e}")
            return 0.0
    
    def calculate_interest_match(self, user_interests, career_description):
        """Calculate matching score between user interests and career description."""
        if not user_interests or not career_description:
            return 0.0
            
        processed_user_interests = self.process_interests(user_interests)
        processed_career_description = self.preprocess_text(career_description)
        
        if not processed_user_interests or not processed_career_description:
            return 0.0
            
        # Create a small corpus with just these two documents
        corpus = [processed_user_interests, processed_career_description]
        
        try:
            # Transform the corpus to TF-IDF feature vectors
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating interest match: {e}")
            return 0.0
    
    def calculate_recommendation_score(self, user_data, career_data, market_trend=None):
        """Calculate overall recommendation score."""
        # Get skill match score (50% weight)
        skill_match_score = self.calculate_skill_match(
            user_data.get('skills', []), 
            career_data.get('required_skills', [])
        )
        
        # Get interest match score (30% weight)
        interest_match_score = self.calculate_interest_match(
            user_data.get('interests', []), 
            career_data.get('description', '')
        )
        
        # Calculate market trend factor (20% weight)
        market_trend_factor = 0.5  # Default to neutral if no market trend data
        if market_trend:
            market_trend_factor = market_trend.get('demand_level', 0.5)
        
        # Calculate weighted score
        weighted_score = (
            0.5 * skill_match_score + 
            0.3 * interest_match_score + 
            0.2 * market_trend_factor
        )
        
        return round(weighted_score * 100, 2)  # Convert to percentage with 2 decimal places
    
    def generate_career_recommendations(self, user_data, careers_data, market_trends=None):
        """Generate career recommendations for a user."""
        recommendations = []
        
        for career_data in careers_data:
            # Get market trend for this career if available
            career_market_trend = next(
                (mt for mt in market_trends if mt.get('career_id') == career_data.get('id')), 
                None
            ) if market_trends else None
            
            # Calculate recommendation score
            score = self.calculate_recommendation_score(user_data, career_data, career_market_trend)
            
            # Add to recommendations list if score is above threshold
            if score > 20:  # Only include careers with at least 20% match
                recommendations.append({
                    'career': career_data,
                    'score': score,
                    'market_trend': career_market_trend
                })
        
        # Sort recommendations by score (descending)
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return recommendations
