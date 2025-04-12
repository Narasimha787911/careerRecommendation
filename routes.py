import os
import logging
from datetime import datetime, date
from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import app, db
from models import User, Skill, Career, Assessment, Recommendation, UserPreference, MarketTrend, Feedback, user_skill, career_skill
from ai_engine import CareerRecommendationEngine
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

# Initialize recommendation engine
recommendation_engine = CareerRecommendationEngine()

@app.route('/')
def index():
    """Home page route"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not username or not name or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
            
        # Check if user already exists
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already exists', 'danger')
            return render_template('register.html')
            
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            flash('Username already exists', 'danger')
            return render_template('register.html')
            
        # Create new user
        new_user = User(username=username, name=name, email=email)
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during registration: {e}")
            flash('An error occurred during registration', 'danger')
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if request.method == 'POST':
        login_id = request.form.get('login_id')
        password = request.form.get('password')
        
        # Check if login_id is an email or username
        if '@' in login_id:
            user = User.query.filter_by(email=login_id).first()
        else:
            user = User.query.filter_by(username=login_id).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username/email or password', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout route"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard route"""
    # Get user's latest assessment and recommendations
    latest_assessment = Assessment.query.filter_by(user_id=current_user.id).order_by(Assessment.date_taken.desc()).first()
    recommendations = []
    
    if latest_assessment:
        recommendations = Recommendation.query.filter_by(assessment_id=latest_assessment.id).order_by(Recommendation.match_score.desc()).all()
    
    return render_template('dashboard.html', 
                          assessment=latest_assessment, 
                          recommendations=recommendations)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile route"""
    # Get user skills
    user_skills = current_user.skills.all() if hasattr(current_user, 'skills') else []
    all_skills = Skill.query.all()
    
    # Get or create user preferences
    preferences = UserPreference.query.filter_by(user_id=current_user.id).first()
    if not preferences:
        preferences = UserPreference(user_id=current_user.id)
        db.session.add(preferences)
        db.session.commit()
    
    if request.method == 'POST':
        # Update profile information
        current_user.name = request.form.get('name')
        current_user.age = request.form.get('age', type=int)
        current_user.education = request.form.get('education')
        current_user.experience = request.form.get('experience')
        current_user.interests = request.form.get('interests')
        
        # Update skills
        selected_skill_ids = request.form.getlist('skills')
        selected_skills = Skill.query.filter(Skill.id.in_(selected_skill_ids)).all()
        
        # Clear existing skills and add the selected ones
        current_user.skills = []
        for skill in selected_skills:
            current_user.skills.append(skill)
        
        # Update preferences
        preferences.salary_preference = request.form.get('salary_preference')
        preferences.location_preference = request.form.get('location_preference')
        preferences.remote_work = 'remote_work' in request.form
        
        try:
            preferences.work_life_balance = int(request.form.get('work_life_balance', 5))
            preferences.job_security = int(request.form.get('job_security', 5))
            preferences.growth_opportunity = int(request.form.get('growth_opportunity', 5))
        except (ValueError, TypeError):
            flash('Invalid values for preference scales', 'warning')
        
        try:
            db.session.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating profile: {e}")
            flash('An error occurred while updating your profile', 'danger')
    
    return render_template('profile.html', 
                          user=current_user, 
                          user_skills=user_skills,
                          all_skills=all_skills,
                          preferences=preferences)

@app.route('/assessment', methods=['GET', 'POST'])
@login_required
def assessment():
    """Career assessment route"""
    if request.method == 'POST':
        # Create new assessment
        personality_traits = request.form.get('personality_traits')
        interests = request.form.get('interests')
        strengths = request.form.get('strengths')
        weaknesses = request.form.get('weaknesses')
        
        new_assessment = Assessment(
            user_id=current_user.id,
            personality_traits=personality_traits,
            interests=interests,
            strengths=strengths,
            weaknesses=weaknesses
        )
        
        try:
            db.session.add(new_assessment)
            db.session.commit()
            
            # Generate recommendations
            return redirect(url_for('generate_recommendations', assessment_id=new_assessment.id))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating assessment: {e}")
            flash('An error occurred while saving your assessment', 'danger')
    
    return render_template('assessment.html')

@app.route('/generate_recommendations/<int:assessment_id>')
@login_required
def generate_recommendations(assessment_id):
    """Generate career recommendations based on assessment"""
    assessment = Assessment.query.get_or_404(assessment_id)
    
    # Check if user has permission to access this assessment
    if assessment.user_id != current_user.id:
        flash('You do not have permission to access this assessment', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if recommendation engine is initialized
    all_careers = Career.query.all()
    if not all_careers:
        flash('No career data is available. Please try again later.', 'warning')
        return redirect(url_for('dashboard'))
        
    # Initialize recommendation engine if needed
    if not recommendation_engine.careers:
        recommendation_engine.create_career_vectors(all_careers)
    
    # Prepare user data
    user_data = {
        'skills': current_user.skills.all() if hasattr(current_user, 'skills') else [],
        'interests': assessment.interests,
        'strengths': assessment.strengths,
        'personality_traits': assessment.personality_traits,
        'education_level': current_user.education,
        'preferences': UserPreference.query.filter_by(user_id=current_user.id).first()
    }
    
    try:
        # Get recommendations
        career_recommendations = recommendation_engine.get_career_recommendations(user_data, top_n=5)
        
        # Save recommendations to database
        for career, score, reasoning in career_recommendations:
            new_recommendation = Recommendation(
                assessment_id=assessment.id,
                career_id=career.id,
                match_score=score,
                reasoning=reasoning
            )
            db.session.add(new_recommendation)
            
        db.session.commit()
        flash('Recommendations generated successfully', 'success')
        return redirect(url_for('recommendations', assessment_id=assessment.id))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error generating recommendations: {e}")
        flash('An error occurred while generating recommendations', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/recommendations/<int:assessment_id>')
@login_required
def recommendations(assessment_id):
    """View recommendations for an assessment"""
    assessment = Assessment.query.get_or_404(assessment_id)
    
    # Check if user has permission to access this assessment
    if assessment.user_id != current_user.id:
        flash('You do not have permission to access this assessment', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get recommendations
    recommendations = Recommendation.query.filter_by(assessment_id=assessment.id).order_by(Recommendation.match_score.desc()).all()
    
    return render_template('recommendations.html', 
                          assessment=assessment,
                          recommendations=recommendations)

@app.route('/career/<int:career_id>')
@login_required
def career_details(career_id):
    """View career details"""
    career = Career.query.get_or_404(career_id)
    
    # Get market trends
    trends = MarketTrend.query.filter_by(career_id=career.id).order_by(MarketTrend.year).all()
    
    # Generate trend charts if there is trend data
    charts = {}
    if trends:
        charts = generate_trend_charts(trends)
    
    return render_template('career_details.html', 
                          career=career,
                          trends=trends,
                          charts=charts)

@app.route('/feedback/<int:recommendation_id>', methods=['POST'])
@login_required
def submit_feedback(recommendation_id):
    """Submit feedback for a recommendation"""
    recommendation = Recommendation.query.get_or_404(recommendation_id)
    
    # Check if the recommendation belongs to the current user
    assessment = Assessment.query.get(recommendation.assessment_id)
    if assessment.user_id != current_user.id:
        flash('You do not have permission to provide feedback for this recommendation', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get feedback data
    rating = request.form.get('rating')
    comments = request.form.get('comments')
    
    # Validate rating
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
    except (TypeError, ValueError):
        flash('Invalid rating value. Please provide a rating between 1 and 5.', 'danger')
        return redirect(url_for('recommendations', assessment_id=assessment.id))
    
    # Check if feedback already exists
    existing_feedback = Feedback.query.filter_by(user_id=current_user.id, recommendation_id=recommendation_id).first()
    
    if existing_feedback:
        # Update existing feedback
        existing_feedback.rating = rating
        existing_feedback.comments = comments
        existing_feedback.submitted_at = datetime.utcnow()
        flash('Feedback updated successfully', 'success')
    else:
        # Create new feedback
        new_feedback = Feedback(
            user_id=current_user.id,
            recommendation_id=recommendation_id,
            rating=rating,
            comments=comments
        )
        db.session.add(new_feedback)
        flash('Feedback submitted successfully', 'success')
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting feedback: {e}")
        flash('An error occurred while submitting your feedback', 'danger')
    
    return redirect(url_for('recommendations', assessment_id=assessment.id))

@app.route('/market_trends/<int:career_id>')
@login_required
def market_trends(career_id):
    """View market trends for a career"""
    career = Career.query.get_or_404(career_id)
    
    # Get trend analysis
    trend_analysis = recommendation_engine.analyze_career_market_trends(career_id)
    
    if 'error' in trend_analysis:
        flash(trend_analysis['error'], 'warning')
        return redirect(url_for('career_details', career_id=career_id))
    
    # Generate trend charts
    charts = generate_trend_analysis_charts(trend_analysis)
    
    return render_template('market_trends.html',
                          career=career,
                          trend_analysis=trend_analysis,
                          charts=charts)

def generate_trend_charts(trends):
    """Generate charts for market trends"""
    charts = {}
    
    # Prepare data
    years = [trend.year for trend in trends]
    demand_levels = [trend.demand_level for trend in trends]
    salary_trends = [trend.salary_trend for trend in trends]
    job_counts = [trend.job_posting_count for trend in trends]
    
    # Generate demand level chart
    plt.figure(figsize=(10, 6))
    plt.plot(years, demand_levels, marker='o', linestyle='-', color='#4CAF50')
    plt.title('Demand Level Trend')
    plt.xlabel('Year')
    plt.ylabel('Demand Level (0-1)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Save to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    demand_chart = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    # Generate salary trend chart
    plt.figure(figsize=(10, 6))
    plt.plot(years, salary_trends, marker='o', linestyle='-', color='#2196F3')
    plt.title('Salary Change Trend')
    plt.xlabel('Year')
    plt.ylabel('Salary Change (%)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Save to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    salary_chart = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    # Generate job posting chart
    plt.figure(figsize=(10, 6))
    plt.plot(years, job_counts, marker='o', linestyle='-', color='#FFC107')
    plt.title('Job Posting Count Trend')
    plt.xlabel('Year')
    plt.ylabel('Number of Job Postings')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Save to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    job_chart = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    charts['demand_chart'] = demand_chart
    charts['salary_chart'] = salary_chart
    charts['job_chart'] = job_chart
    
    return charts

def generate_trend_analysis_charts(trend_analysis):
    """Generate charts for trend analysis"""
    charts = {}
    
    # Extract data
    years = trend_analysis['years_analyzed']
    demand_levels = trend_analysis['demand_levels']
    salary_trends = trend_analysis['salary_trends']
    job_counts = trend_analysis['job_posting_counts']
    
    # Generate combined chart
    plt.figure(figsize=(12, 8))
    
    # Create 3 subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    
    # Demand level subplot
    ax1.plot(years, demand_levels, marker='o', linestyle='-', color='#4CAF50', linewidth=2)
    ax1.set_title('Demand Level Trend', fontsize=14)
    ax1.set_ylabel('Demand Level (0-1)', fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # Salary trend subplot
    ax2.plot(years, salary_trends, marker='o', linestyle='-', color='#2196F3', linewidth=2)
    ax2.set_title('Salary Change Trend', fontsize=14)
    ax2.set_ylabel('Salary Change (%)', fontsize=12)
    ax2.grid(True, linestyle='--', alpha=0.7)
    
    # Job posting subplot
    ax3.plot(years, job_counts, marker='o', linestyle='-', color='#FFC107', linewidth=2)
    ax3.set_title('Job Posting Count', fontsize=14)
    ax3.set_xlabel('Year', fontsize=12)
    ax3.set_ylabel('Number of Postings', fontsize=12)
    ax3.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    
    # Save to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    combined_chart = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    charts['combined_chart'] = combined_chart
    
    return charts

@app.route('/admin/initialize_database')
def initialize_database():
    """Initialize database with sample data (for development/testing only)"""
    # Check if database is already initialized
    if Career.query.count() > 0:
        flash('Database already initialized', 'info')
        return redirect(url_for('index'))
    
    try:
        # Create skills
        skills = [
            Skill(name="Python Programming", description="Proficiency in Python programming language", category="Technical"),
            Skill(name="Data Analysis", description="Ability to analyze and interpret complex data", category="Technical"),
            Skill(name="Machine Learning", description="Knowledge of machine learning algorithms and frameworks", category="Technical"),
            Skill(name="SQL", description="Database query language skills", category="Technical"),
            Skill(name="Communication", description="Excellent verbal and written communication", category="Soft"),
            Skill(name="Project Management", description="Planning, organizing, and managing resources", category="Soft"),
            Skill(name="Problem Solving", description="Ability to identify and solve complex problems", category="Soft"),
            Skill(name="Teamwork", description="Ability to work effectively in a team", category="Soft"),
            Skill(name="Customer Service", description="Providing assistance and support to customers", category="Soft"),
            Skill(name="JavaScript", description="Proficiency in JavaScript programming", category="Technical"),
            Skill(name="HTML/CSS", description="Web development skills", category="Technical"),
            Skill(name="UX/UI Design", description="User experience and interface design", category="Technical"),
            Skill(name="Financial Analysis", description="Analyzing financial data and markets", category="Domain"),
            Skill(name="Marketing", description="Promoting products or services", category="Domain"),
            Skill(name="Healthcare Knowledge", description="Understanding of healthcare systems and practices", category="Domain")
        ]
        db.session.add_all(skills)
        db.session.commit()
        
        # Create careers
        careers = [
            Career(
                title="Data Scientist",
                description="Analyze complex data and build predictive models to help organizations make better decisions.",
                avg_salary=115000.0,
                growth_rate=15.0,
                education_required="Bachelor's or Master's degree in Computer Science, Statistics, or related field",
                experience_required="2-5 years",
                job_outlook="Excellent job prospects due to the growing demand for data-driven insights across industries.",
                work_environment="Typically office-based, with remote work options often available."
            ),
            Career(
                title="Software Engineer",
                description="Design, develop, and maintain software applications and systems.",
                avg_salary=105000.0,
                growth_rate=22.0,
                education_required="Bachelor's degree in Computer Science or related field",
                experience_required="0-3 years",
                job_outlook="Strong demand for software engineers across numerous industries.",
                work_environment="Office settings, with increasing remote work opportunities."
            ),
            Career(
                title="UX/UI Designer",
                description="Create user-friendly interfaces and optimize user experiences for websites and applications.",
                avg_salary=85000.0,
                growth_rate=13.0,
                education_required="Bachelor's degree in Design, HCI, or related field",
                experience_required="1-3 years",
                job_outlook="Growing demand as companies focus more on user experience.",
                work_environment="Creative office environments, with remote options available."
            ),
            Career(
                title="Financial Analyst",
                description="Analyze financial data and provide recommendations for business decisions.",
                avg_salary=80000.0,
                growth_rate=6.0,
                education_required="Bachelor's degree in Finance, Economics, or related field",
                experience_required="1-4 years",
                job_outlook="Steady demand across financial services and corporate sectors.",
                work_environment="Office-based, sometimes high-pressure environments."
            ),
            Career(
                title="Marketing Manager",
                description="Develop and implement marketing strategies to promote products or services.",
                avg_salary=75000.0,
                growth_rate=8.0,
                education_required="Bachelor's degree in Marketing, Business, or related field",
                experience_required="3-5 years",
                job_outlook="Consistent demand as companies always need effective marketing.",
                work_environment="Dynamic office environments, sometimes with flexible schedules."
            ),
            Career(
                title="Healthcare Administrator",
                description="Manage healthcare facilities and services to ensure efficient and effective patient care.",
                avg_salary=72000.0,
                growth_rate=17.0,
                education_required="Bachelor's degree in Healthcare Administration or related field",
                experience_required="2-5 years",
                job_outlook="Excellent growth due to aging population and healthcare expansion.",
                work_environment="Healthcare facilities, including hospitals and clinics."
            ),
            Career(
                title="Web Developer",
                description="Build and maintain websites and web applications.",
                avg_salary=78000.0,
                growth_rate=13.0,
                education_required="Associate's or Bachelor's degree in Computer Science or related field",
                experience_required="0-2 years",
                job_outlook="Strong demand as businesses continue to expand online presence.",
                work_environment="Office settings with growing remote opportunities."
            ),
            Career(
                title="Project Manager",
                description="Plan, execute, and close projects while ensuring they are completed on time and within budget.",
                avg_salary=88000.0,
                growth_rate=6.0,
                education_required="Bachelor's degree in Business or related field",
                experience_required="3-5 years",
                job_outlook="Stable demand across various industries.",
                work_environment="Office-based with some on-site presence required."
            )
        ]
        db.session.add_all(careers)
        db.session.commit()
        
        # Associate skills with careers
        # Data Scientist
        careers[0].skills.extend([
            skills[0],  # Python
            skills[1],  # Data Analysis
            skills[2],  # Machine Learning
            skills[3],  # SQL
            skills[4],  # Communication
            skills[6]   # Problem Solving
        ])
        
        # Software Engineer
        careers[1].skills.extend([
            skills[0],  # Python
            skills[3],  # SQL
            skills[6],  # Problem Solving
            skills[7],  # Teamwork
            skills[9],  # JavaScript
            skills[10]  # HTML/CSS
        ])
        
        # UX/UI Designer
        careers[2].skills.extend([
            skills[4],  # Communication
            skills[6],  # Problem Solving
            skills[7],  # Teamwork
            skills[10], # HTML/CSS
            skills[11]  # UX/UI Design
        ])
        
        # Financial Analyst
        careers[3].skills.extend([
            skills[1],  # Data Analysis
            skills[3],  # SQL
            skills[4],  # Communication
            skills[6],  # Problem Solving
            skills[12]  # Financial Analysis
        ])
        
        # Marketing Manager
        careers[4].skills.extend([
            skills[4],  # Communication
            skills[5],  # Project Management
            skills[7],  # Teamwork
            skills[8],  # Customer Service
            skills[13]  # Marketing
        ])
        
        # Healthcare Administrator
        careers[5].skills.extend([
            skills[4],  # Communication
            skills[5],  # Project Management
            skills[7],  # Teamwork
            skills[8],  # Customer Service
            skills[14]  # Healthcare Knowledge
        ])
        
        # Web Developer
        careers[6].skills.extend([
            skills[0],  # Python
            skills[6],  # Problem Solving
            skills[7],  # Teamwork
            skills[9],  # JavaScript
            skills[10]  # HTML/CSS
        ])
        
        # Project Manager
        careers[7].skills.extend([
            skills[4],  # Communication
            skills[5],  # Project Management
            skills[6],  # Problem Solving
            skills[7],  # Teamwork
            skills[8]   # Customer Service
        ])
        
        db.session.commit()
        
        # Create market trends for each career (past 5 years)
        current_year = datetime.now().year
        years = range(current_year - 4, current_year + 1)
        
        for career in careers:
            # Generate realistic trend data for each career
            if career.title == "Data Scientist":
                # High growth field
                demand_base = 0.6
                demand_growth = 0.08
                salary_growth_base = 0.04
                job_posting_base = 5000
                job_posting_growth = 1.2
            elif career.title == "Software Engineer":
                # Consistently high demand
                demand_base = 0.7
                demand_growth = 0.06
                salary_growth_base = 0.035
                job_posting_base = 8000
                job_posting_growth = 1.15
            elif career.title in ["UX/UI Designer", "Web Developer"]:
                # Growing fields
                demand_base = 0.5
                demand_growth = 0.07
                salary_growth_base = 0.03
                job_posting_base = 3000
                job_posting_growth = 1.12
            elif career.title == "Healthcare Administrator":
                # Growth due to aging population
                demand_base = 0.55
                demand_growth = 0.05
                salary_growth_base = 0.025
                job_posting_base = 2500
                job_posting_growth = 1.1
            else:
                # More stable fields
                demand_base = 0.45
                demand_growth = 0.02
                salary_growth_base = 0.015
                job_posting_base = 2000
                job_posting_growth = 1.05
            
            # Create trend data for each year
            trends = []
            for i, year in enumerate(years):
                # Add some randomness to make data more realistic
                random_factor = np.random.normal(1, 0.1)  # Normal distribution with mean 1 and std 0.1
                
                demand = min(0.9, demand_base + (i * demand_growth * random_factor))
                salary_growth = salary_growth_base * random_factor
                job_postings = int(job_posting_base * (job_posting_growth ** i) * random_factor)
                
                trend = MarketTrend(
                    career_id=career.id,
                    year=year,
                    demand_level=demand,
                    salary_trend=salary_growth,
                    job_posting_count=job_postings,
                    source="Bureau of Labor Statistics (simulated)",
                    notes=f"Trend data for {career.title} in {year}"
                )
                trends.append(trend)
            
            db.session.add_all(trends)
        
        db.session.commit()
        flash('Database initialized with sample data', 'success')
        
        # Initialize recommendation engine with careers
        recommendation_engine.create_career_vectors(Career.query.all())
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error initializing database: {e}")
        flash(f'Error initializing database: {str(e)}', 'danger')
    
    return redirect(url_for('index'))


# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500