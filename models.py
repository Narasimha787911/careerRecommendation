from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

# Define User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    skills = db.Column(db.Text, nullable=True)  # Stored as JSON
    education = db.Column(db.Text, nullable=True)  # Stored as JSON
    experience = db.Column(db.Text, nullable=True)  # Stored as JSON
    interests = db.Column(db.Text, nullable=True)  # Stored as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define relationships
    recommendations = db.relationship('Recommendation', backref='user', lazy=True)
    feedbacks = db.relationship('Feedback', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_skills(self):
        if self.skills:
            return json.loads(self.skills)
        return []
    
    def set_skills(self, skills_list):
        self.skills = json.dumps(skills_list)
    
    def get_education(self):
        if self.education:
            return json.loads(self.education)
        return []
    
    def set_education(self, education_list):
        self.education = json.dumps(education_list)
    
    def get_experience(self):
        if self.experience:
            return json.loads(self.experience)
        return []
    
    def set_experience(self, experience_list):
        self.experience = json.dumps(experience_list)
    
    def get_interests(self):
        if self.interests:
            return json.loads(self.interests)
        return []
    
    def set_interests(self, interests_list):
        self.interests = json.dumps(interests_list)
    
    def has_completed_profile(self):
        return bool(self.skills and self.education and self.interests)
    
    def __repr__(self):
        return f'<User {self.name}>'

# Define Career model
class Career(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    required_skills = db.Column(db.Text, nullable=False)  # Stored as JSON
    industry = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define relationships
    recommendations = db.relationship('Recommendation', backref='career', lazy=True)
    market_trends = db.relationship('MarketTrend', backref='career', lazy=True)
    
    def get_required_skills(self):
        return json.loads(self.required_skills)
    
    def set_required_skills(self, skills_list):
        self.required_skills = json.dumps(skills_list)
    
    def __repr__(self):
        return f'<Career {self.name}>'

# Define Recommendation model
class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    career_id = db.Column(db.Integer, db.ForeignKey('career.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    date_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define relationships
    feedbacks = db.relationship('Feedback', backref='recommendation', lazy=True)
    
    def __repr__(self):
        return f'<Recommendation {self.id} for User {self.user_id}>'

# Define Feedback model
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recommendation_id = db.Column(db.Integer, db.ForeignKey('recommendation.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # Scale of 1-5
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Feedback {self.id} from User {self.user_id}>'

# Define MarketTrend model
class MarketTrend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    career_id = db.Column(db.Integer, db.ForeignKey('career.id'), nullable=False)
    demand_level = db.Column(db.Float, nullable=False)  # Scale of 0-1
    salary_range = db.Column(db.String(50), nullable=False)  # E.g., "50000-70000"
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MarketTrend {self.id} for Career {self.career_id}>'

# Define AI Model entity
class AIModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    algorithm = db.Column(db.String(100), nullable=False)
    accuracy = db.Column(db.Float, nullable=False)  # Scale of 0-1
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<AIModel {self.name}>'
