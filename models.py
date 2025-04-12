from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

# Association tables
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
    username = db.Column(db.String(64), unique=True)
    name = db.Column(db.String(128))
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(256))
    age = db.Column(db.Integer)
    interests = db.Column(db.Text)
    skills = db.Column(db.Text)
    education = db.Column(db.Text)
    experience = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assessments = db.relationship('Assessment', backref='user', lazy='dynamic')
    preferences = db.relationship('UserPreference', backref='user', uselist=False)
    feedbacks = db.relationship('Feedback', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.name}>'

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(64))  # Technical, Soft, Domain-specific, etc.
    
    def __repr__(self):
        return f'<Skill {self.name}>'

class Career(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Renamed from title to match DB
    description = db.Column(db.Text, nullable=False)
    required_skills = db.Column(db.Text, nullable=False)  # Skills as text
    industry = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime)
    
    # Relationships
    skills = db.relationship('Skill', secondary=career_skill, backref=db.backref('careers', lazy='dynamic'))
    market_trends = db.relationship('MarketTrend', backref='career', lazy='dynamic')
    
    @property
    def title(self):
        """For backward compatibility with existing code"""
        return self.name
    
    @property
    def avg_salary(self):
        """Calculate average salary from market trends"""
        trends = self.market_trends.all()
        if not trends:
            return 0
        latest_trend = max(trends, key=lambda t: t.year) if trends else None
        return latest_trend.salary_trend if latest_trend else 0
    
    @property
    def growth_rate(self):
        """Calculate growth rate from market trends"""
        trends = self.market_trends.all()
        if len(trends) < 2:
            return 0
        sorted_trends = sorted(trends, key=lambda t: t.year, reverse=True)
        if len(sorted_trends) >= 2:
            latest = sorted_trends[0]
            previous = sorted_trends[1]
            if previous.demand_level > 0:
                return ((latest.demand_level - previous.demand_level) / previous.demand_level) * 100
        return 0
    
    @property
    def education_required(self):
        """Extract education requirements from description"""
        # Simple implementation - in a real app, you'd use NLP to extract this
        return "Bachelor's Degree"
    
    @property
    def experience_required(self):
        """Extract experience requirements from description"""
        # Simple implementation - in a real app, you'd use NLP to extract this
        return "2-5 years"
    
    @property
    def job_outlook(self):
        """Generate job outlook from market trends"""
        trends = self.market_trends.all()
        if not trends:
            return "No data available"
        
        latest_trend = max(trends, key=lambda t: t.year) if trends else None
        if not latest_trend:
            return "No data available"
        
        if latest_trend.demand_level > 0.7:
            return "Excellent job outlook with high demand"
        elif latest_trend.demand_level > 0.5:
            return "Good job outlook with steady demand"
        elif latest_trend.demand_level > 0.3:
            return "Moderate job outlook"
        else:
            return "Limited job outlook"
    
    @property
    def work_environment(self):
        """Return work environment information"""
        # Simple implementation
        return f"Typical work environment in {self.industry} industry"
        
    def __repr__(self):
        return f'<Career {self.name}>'

class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)
    personality_traits = db.Column(db.String(256))  # JSON string or comma-separated values
    interests = db.Column(db.String(256))  # JSON string or comma-separated values
    strengths = db.Column(db.String(256))  # JSON string or comma-separated values
    weaknesses = db.Column(db.String(256))  # JSON string or comma-separated values
    
    def __repr__(self):
        return f'<Assessment {self.id} for User {self.user_id}>'

class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    career_id = db.Column(db.Integer, db.ForeignKey('career.id'), nullable=False)
    score = db.Column(db.Float)  # Percentage match
    date_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    career = db.relationship('Career')
    
    def __repr__(self):
        return f'<Recommendation {self.id} for User {self.user_id}>'

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
    demand_level = db.Column(db.Float, nullable=False)  # Scale 0-1
    salary_range = db.Column(db.String(50), nullable=False)  # Renamed from salary_trend
    updated_at = db.Column(db.DateTime)  # Instead of year field
    
    # Virtual properties to maintain compatibility with existing code
    @property
    def year(self):
        """Calculate year from updated_at"""
        if self.updated_at:
            return self.updated_at.year
        return 2025  # Default to current year
    
    @property
    def salary_trend(self):
        """Extract numeric salary trend from salary_range"""
        if not self.salary_range:
            return 0
        
        # Try to extract a percentage or number
        try:
            # If it's a range like "50000-70000"
            if '-' in self.salary_range:
                low, high = self.salary_range.split('-')
                return (float(high) - float(low)) / float(low) * 100  # Percentage increase
            
            # If it's just a percentage like "5%" or "5"
            return float(self.salary_range.strip('%'))
        except:
            return 0
    
    @property
    def job_posting_count(self):
        """Calculated based on demand level as we don't have actual data"""
        return int(1000 * self.demand_level)
    
    @property
    def source(self):
        """Default source information"""
        return "Career Recommendation System"
    
    @property
    def notes(self):
        """Default notes"""
        return None
    
    def __repr__(self):
        year_str = self.year if hasattr(self, 'updated_at') and self.updated_at else "Unknown"
        return f'<MarketTrend for Career {self.career_id} in {year_str}>'

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recommendation_id = db.Column(db.Integer, db.ForeignKey('recommendation.id'))
    rating = db.Column(db.Integer)  # Scale 1-5
    comments = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    recommendation = db.relationship('Recommendation')
    
    def __repr__(self):
        return f'<Feedback {self.id} from User {self.user_id}>'