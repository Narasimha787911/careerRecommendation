from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import logging

from app import app, db
from models import User, Skill, Career, Assessment, Recommendation, UserPreference, MarketTrend, Feedback
from ai_engine import CareerRecommendationEngine

# Set up logging
logger = logging.getLogger(__name__)

# Initialize the recommendation engine
recommendation_engine = CareerRecommendationEngine()

@app.route('/')
def index():
    """Home page route"""
    careers_count = Career.query.count()
    return render_template('index.html', careers_count=careers_count)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Basic validation
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
            
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')
            
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('register.html')
            
        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in', 'success')
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
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout route"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard route"""
    # Get user's latest assessment and recommendations
    latest_assessment = Assessment.query.filter_by(user_id=current_user.id).order_by(Assessment.date_taken.desc()).first()
    recommendations = []
    
    if latest_assessment:
        recommendations = Recommendation.query.filter_by(assessment_id=latest_assessment.id).order_by(Recommendation.match_score.desc()).limit(3).all()
    
    return render_template('dashboard.html', 
                          assessment=latest_assessment, 
                          recommendations=recommendations)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile route"""
    # Get user skills
    user_skills = current_user.skills
    # Get all available skills
    all_skills = Skill.query.all()
    
    # Get or create user preferences
    preferences = UserPreference.query.filter_by(user_id=current_user.id).first()
    if not preferences:
        preferences = UserPreference(user_id=current_user.id)
        db.session.add(preferences)
        db.session.commit()
    
    if request.method == 'POST':
        # Update user profile
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        
        try:
            dob_str = request.form.get('date_of_birth')
            if dob_str:
                current_user.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format', 'danger')
            
        current_user.education_level = request.form.get('education_level')
        current_user.bio = request.form.get('bio')
        
        # Update skills
        current_user.skills = []
        skill_ids = request.form.getlist('skills')
        for skill_id in skill_ids:
            skill = Skill.query.get(int(skill_id))
            if skill:
                current_user.skills.append(skill)
                
        # Update preferences
        preferences.salary_preference = request.form.get('salary_preference')
        preferences.location_preference = request.form.get('location_preference')
        preferences.remote_work = 'remote_work' in request.form
        
        try:
            preferences.work_life_balance = int(request.form.get('work_life_balance', 5))
            preferences.job_security = int(request.form.get('job_security', 5))
            preferences.growth_opportunity = int(request.form.get('growth_opportunity', 5))
        except ValueError:
            flash('Invalid preference values', 'danger')
        
        try:
            db.session.commit()
            flash('Profile updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating profile: {e}")
            flash('An error occurred while updating your profile', 'danger')
    
    return render_template('profile.html', 
                          user=current_user, 
                          preferences=preferences,
                          user_skills=user_skills,
                          all_skills=all_skills)

@app.route('/assessment', methods=['GET', 'POST'])
@login_required
def assessment():
    """Career assessment route"""
    if request.method == 'POST':
        # Get assessment data
        personality_traits = request.form.get('personality_traits')
        interests = request.form.get('interests')
        strengths = request.form.get('strengths')
        weaknesses = request.form.get('weaknesses')
        
        # Create new assessment
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
            logger.error(f"Error saving assessment: {e}")
            flash('An error occurred while saving your assessment', 'danger')
    
    return render_template('assessment.html')

@app.route('/generate_recommendations/<int:assessment_id>')
@login_required
def generate_recommendations(assessment_id):
    """Generate career recommendations based on assessment"""
    assessment = Assessment.query.get_or_404(assessment_id)
    
    # Ensure the assessment belongs to the current user
    if assessment.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if recommendations already exist
    existing_recommendations = Recommendation.query.filter_by(assessment_id=assessment_id).first()
    if existing_recommendations:
        return redirect(url_for('recommendations', assessment_id=assessment_id))
    
    # Prepare data for recommendation engine
    careers = Career.query.all()
    
    # Initialize the recommendation engine with career data if needed
    if not recommendation_engine.careers:
        try:
            # Try to load saved model first
            if not recommendation_engine.load_model():
                # If loading fails, create new vectors
                recommendation_engine.create_career_vectors(careers)
        except Exception as e:
            logger.error(f"Error initializing recommendation engine: {e}")
            flash('An error occurred while generating recommendations', 'danger')
            return redirect(url_for('dashboard'))
    
    # Create user data dictionary
    user_data = {
        'skills': current_user.skills,
        'interests': assessment.interests,
        'strengths': assessment.strengths,
        'personality_traits': assessment.personality_traits,
        'education_level': current_user.education_level,
        'preferences': UserPreference.query.filter_by(user_id=current_user.id).first()
    }
    
    try:
        # Get recommendations
        recommended_careers = recommendation_engine.get_career_recommendations(user_data, top_n=5)
        
        # Save recommendations to database
        for career, score, reasoning in recommended_careers:
            recommendation = Recommendation(
                assessment_id=assessment_id,
                career_id=career.id,
                match_score=score,
                reasoning=reasoning
            )
            db.session.add(recommendation)
            
        db.session.commit()
        
        # Try to save the model for future use
        recommendation_engine.save_model()
        
        return redirect(url_for('recommendations', assessment_id=assessment_id))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error generating recommendations: {e}")
        flash('An error occurred while generating recommendations', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/recommendations/<int:assessment_id>')
@login_required
def recommendations(assessment_id):
    """Display career recommendations"""
    assessment = Assessment.query.get_or_404(assessment_id)
    
    # Ensure the assessment belongs to the current user
    if assessment.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get recommendations
    recommendations = Recommendation.query.filter_by(assessment_id=assessment_id).order_by(Recommendation.match_score.desc()).all()
    
    return render_template('recommendations.html', 
                          assessment=assessment,
                          recommendations=recommendations)

@app.route('/career/<int:career_id>')
def career_details(career_id):
    """Display career details"""
    career = Career.query.get_or_404(career_id)
    
    # Get market trends
    market_trends = MarketTrend.query.filter_by(career_id=career_id).order_by(MarketTrend.year).all()
    
    # Analyze trends if they exist
    trend_analysis = None
    if market_trends:
        try:
            trend_analysis = recommendation_engine.analyze_career_market_trends(career_id)
        except Exception as e:
            logger.error(f"Error analyzing market trends: {e}")
    
    return render_template('career_details.html', 
                          career=career,
                          market_trends=market_trends,
                          trend_analysis=trend_analysis)

@app.route('/submit_feedback', methods=['POST'])
@login_required
def submit_feedback():
    """Submit feedback for a recommendation"""
    recommendation_id = request.form.get('recommendation_id')
    rating = request.form.get('rating')
    comments = request.form.get('comments')
    
    # Validate data
    if not recommendation_id or not rating:
        flash('Rating is required', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        rating = int(rating)
    except ValueError:
        flash('Invalid rating', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if recommendation exists and belongs to the user
    recommendation = Recommendation.query.get(recommendation_id)
    if not recommendation or recommendation.assessment.user_id != current_user.id:
        flash('Invalid recommendation', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if feedback already exists
    existing_feedback = Feedback.query.filter_by(
        user_id=current_user.id,
        recommendation_id=recommendation_id
    ).first()
    
    if existing_feedback:
        # Update existing feedback
        existing_feedback.rating = rating
        existing_feedback.comments = comments
    else:
        # Create new feedback
        new_feedback = Feedback(
            user_id=current_user.id,
            recommendation_id=recommendation_id,
            rating=rating,
            comments=comments
        )
        db.session.add(new_feedback)
    
    try:
        db.session.commit()
        flash('Feedback submitted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting feedback: {e}")
        flash('An error occurred while submitting feedback', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/admin/seed_data')
def seed_data():
    """Seed the database with initial data (for development purposes)"""
    # Check if data already exists
    if Skill.query.count() > 0 or Career.query.count() > 0:
        flash('Database already contains data', 'info')
        return redirect(url_for('index'))
    
    try:
        # Create skills
        skills = [
            Skill(name='Python Programming', description='Experience with Python programming language', category='Technical'),
            Skill(name='Data Analysis', description='Ability to analyze and interpret complex data', category='Technical'),
            Skill(name='Machine Learning', description='Experience with machine learning algorithms and tools', category='Technical'),
            Skill(name='Communication', description='Excellent written and verbal communication skills', category='Soft'),
            Skill(name='Problem Solving', description='Ability to solve complex problems', category='Soft'),
            Skill(name='Project Management', description='Experience managing projects and teams', category='Soft'),
            Skill(name='JavaScript', description='Experience with JavaScript programming language', category='Technical'),
            Skill(name='Web Development', description='Experience building web applications', category='Technical'),
            Skill(name='SQL', description='Experience with SQL databases', category='Technical'),
            Skill(name='Leadership', description='Ability to lead and motivate teams', category='Soft'),
            Skill(name='Critical Thinking', description='Ability to analyze situations and make decisions', category='Soft'),
            Skill(name='Marketing', description='Experience with marketing strategies and campaigns', category='Domain-specific'),
            Skill(name='Financial Analysis', description='Experience analyzing financial data and reports', category='Domain-specific'),
            Skill(name='Sales', description='Experience with sales techniques and customer relationships', category='Domain-specific'),
            Skill(name='Graphic Design', description='Experience with graphic design tools and principles', category='Technical'),
        ]
        
        db.session.add_all(skills)
        db.session.commit()
        
        # Create careers
        careers = [
            Career(
                title='Data Scientist',
                description='Analyze large datasets and build predictive models to help organizations make data-driven decisions.',
                avg_salary=120000,
                growth_rate=16.0,
                education_required='Bachelor\'s or Master\'s degree in Computer Science, Statistics, or related field',
                experience_required='2-5 years',
                job_outlook='Very positive outlook with high demand across industries',
                work_environment='Office environment, sometimes remote'
            ),
            Career(
                title='Software Engineer',
                description='Design, develop, and maintain software applications and systems.',
                avg_salary=110000,
                growth_rate=22.0,
                education_required='Bachelor\'s degree in Computer Science or related field',
                experience_required='0-3 years',
                job_outlook='Strong job growth expected due to increasing demand for software',
                work_environment='Office environment, often remote'
            ),
            Career(
                title='Marketing Manager',
                description='Develop and implement marketing strategies to promote products or services.',
                avg_salary=85000,
                growth_rate=8.0,
                education_required='Bachelor\'s degree in Marketing, Business, or related field',
                experience_required='3-5 years',
                job_outlook='Steady growth as companies focus on digital marketing',
                work_environment='Office environment, sometimes remote'
            ),
            Career(
                title='Financial Analyst',
                description='Analyze financial data and make recommendations for investment decisions.',
                avg_salary=95000,
                growth_rate=5.0,
                education_required='Bachelor\'s degree in Finance, Economics, or related field',
                experience_required='1-3 years',
                job_outlook='Stable job market with opportunities in various industries',
                work_environment='Office environment, sometimes remote'
            ),
            Career(
                title='UX/UI Designer',
                description='Design user interfaces and experiences for websites and applications.',
                avg_salary=90000,
                growth_rate=13.0,
                education_required='Bachelor\'s degree in Design, HCI, or related field',
                experience_required='2-4 years',
                job_outlook='Growing demand as companies focus on user experience',
                work_environment='Office environment, often remote'
            ),
        ]
        
        db.session.add_all(careers)
        db.session.commit()
        
        # Associate skills with careers
        data_scientist = Career.query.filter_by(title='Data Scientist').first()
        if data_scientist:
            data_scientist.skills.extend([
                Skill.query.filter_by(name='Python Programming').first(),
                Skill.query.filter_by(name='Data Analysis').first(),
                Skill.query.filter_by(name='Machine Learning').first(),
                Skill.query.filter_by(name='SQL').first(),
                Skill.query.filter_by(name='Problem Solving').first(),
                Skill.query.filter_by(name='Communication').first()
            ])
            
        software_engineer = Career.query.filter_by(title='Software Engineer').first()
        if software_engineer:
            software_engineer.skills.extend([
                Skill.query.filter_by(name='Python Programming').first(),
                Skill.query.filter_by(name='JavaScript').first(),
                Skill.query.filter_by(name='Web Development').first(),
                Skill.query.filter_by(name='SQL').first(),
                Skill.query.filter_by(name='Problem Solving').first(),
                Skill.query.filter_by(name='Project Management').first()
            ])
            
        marketing_manager = Career.query.filter_by(title='Marketing Manager').first()
        if marketing_manager:
            marketing_manager.skills.extend([
                Skill.query.filter_by(name='Marketing').first(),
                Skill.query.filter_by(name='Communication').first(),
                Skill.query.filter_by(name='Leadership').first(),
                Skill.query.filter_by(name='Project Management').first(),
                Skill.query.filter_by(name='Critical Thinking').first()
            ])
            
        financial_analyst = Career.query.filter_by(title='Financial Analyst').first()
        if financial_analyst:
            financial_analyst.skills.extend([
                Skill.query.filter_by(name='Financial Analysis').first(),
                Skill.query.filter_by(name='Data Analysis').first(),
                Skill.query.filter_by(name='Critical Thinking').first(),
                Skill.query.filter_by(name='Problem Solving').first(),
                Skill.query.filter_by(name='Communication').first()
            ])
            
        ux_designer = Career.query.filter_by(title='UX/UI Designer').first()
        if ux_designer:
            ux_designer.skills.extend([
                Skill.query.filter_by(name='Graphic Design').first(),
                Skill.query.filter_by(name='Web Development').first(),
                Skill.query.filter_by(name='Communication').first(),
                Skill.query.filter_by(name='Problem Solving').first(),
                Skill.query.filter_by(name='Critical Thinking').first()
            ])
            
        # Add market trends for each career
        current_year = datetime.now().year
        
        for career in careers:
            # Create market trends for the past 5 years
            for i in range(5):
                year = current_year - 4 + i
                growth_factor = 1.0 + (i * 0.05)  # Increasing trend
                
                trend = MarketTrend(
                    career_id=career.id,
                    year=year,
                    demand_level=min(0.3 + (i * 0.1), 1.0),  # Increasing demand (0-1 scale)
                    salary_trend=0.02 + (i * 0.005),  # Increasing salary growth rate
                    job_posting_count=int(1000 * growth_factor * (1 + (career.growth_rate / 100))),
                    source='Bureau of Labor Statistics',
                    notes=f'Market data for {career.title} in {year}'
                )
                db.session.add(trend)
        
        db.session.commit()
        flash('Database seeded successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error seeding database: {e}")
        flash(f'Error seeding database: {str(e)}', 'danger')
        
    return redirect(url_for('index'))