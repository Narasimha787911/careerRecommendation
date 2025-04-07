from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db

# Association tables for many-to-many relationships
user_skill = db.Table('user_skill',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skill.id'), primary_key=True)
)

career_skill = db.Table('career_skill',
    db.Column('career_id', db.Integer, db.ForeignKey('career.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skill.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    date_of_birth = db.Column(db.Date)
    education_level = db.Column(db.String(64))
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    skills = db.relationship('Skill', secondary=user_skill, backref=db.backref('users', lazy='dynamic'))
    assessments = db.relationship('Assessment', backref='user', lazy='dynamic')
    preferences = db.relationship('UserPreference', backref='user', uselist=False)
    feedbacks = db.relationship('Feedback', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(64))  # Technical, Soft, Domain-specific, etc.
    
    def __repr__(self):
        return f'<Skill {self.name}>'

class Career(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    avg_salary = db.Column(db.Float)
    growth_rate = db.Column(db.Float)  # Annual growth rate as a percentage
    education_required = db.Column(db.String(64))
    experience_required = db.Column(db.String(64))
    job_outlook = db.Column(db.Text)
    work_environment = db.Column(db.Text)
    
    # Relationships
    skills = db.relationship('Skill', secondary=career_skill, backref=db.backref('careers', lazy='dynamic'))
    market_trends = db.relationship('MarketTrend', backref='career', lazy='dynamic')
    
    def __repr__(self):
        return f'<Career {self.title}>'

class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)
    personality_traits = db.Column(db.String(256))  # JSON string or comma-separated values
    interests = db.Column(db.String(256))  # JSON string or comma-separated values
    strengths = db.Column(db.String(256))  # JSON string or comma-separated values
    weaknesses = db.Column(db.String(256))  # JSON string or comma-separated values
    
    # Relationships
    recommendations = db.relationship('Recommendation', backref='assessment', lazy='dynamic')
    
    def __repr__(self):
        return f'<Assessment for User {self.user_id} on {self.date_taken}>'

class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment.id'), nullable=False)
    career_id = db.Column(db.Integer, db.ForeignKey('career.id'), nullable=False)
    match_score = db.Column(db.Float)  # Percentage match
    reasoning = db.Column(db.Text)  # Explanation for the recommendation
    date_generated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    career = db.relationship('Career')
    
    def __repr__(self):
        return f'<Recommendation for Assessment {self.assessment_id}, Career {self.career_id}>'

class UserPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    salary_preference = db.Column(db.String(64))  # Range like "50000-70000"
    location_preference = db.Column(db.String(128))
    remote_work = db.Column(db.Boolean, default=False)
    work_life_balance = db.Column(db.Integer)  # Scale 1-10
    job_security = db.Column(db.Integer)  # Scale 1-10
    growth_opportunity = db.Column(db.Integer)  # Scale 1-10
    
    def __repr__(self):
        return f'<UserPreference for User {self.user_id}>'

class MarketTrend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    career_id = db.Column(db.Integer, db.ForeignKey('career.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    demand_level = db.Column(db.Float)  # Scale 0-1
    salary_trend = db.Column(db.Float)  # Percentage change
    job_posting_count = db.Column(db.Integer)
    source = db.Column(db.String(128))
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<MarketTrend for Career {self.career_id} in {self.year}>'

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recommendation_id = db.Column(db.Integer, db.ForeignKey('recommendation.id'))
    rating = db.Column(db.Integer)  # Scale 1-5
    comments = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    recommendation = db.relationship('Recommendation')
    
    def __repr__(self):
        return f'<Feedback from User {self.user_id} on Recommendation {self.recommendation_id}>'