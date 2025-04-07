from flask import render_template, url_for, flash, redirect, request, jsonify, session
from flask_login import login_user, current_user, logout_user, login_required
from app import app, db
from models import User, Career, Recommendation, Feedback, MarketTrend, AIModel
from werkzeug.security import generate_password_hash, check_password_hash
from ai_engine import CareerRecommendationEngine
from datetime import datetime
import json
import logging

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize AI Engine
recommendation_engine = CareerRecommendationEngine()

# Routes
@app.route('/')
def index():
    return render_template('index.html', title='AI Career Recommendation System')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if not name or not email or not password:
            flash('All fields are required!', 'danger')
            return render_template('register.html', title='Register')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html', title='Register')
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already registered!', 'danger')
            return render_template('register.html', title='Register')
        
        # Create new user
        new_user = User(name=name, email=email)
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering user: {e}")
            flash('An error occurred during registration. Please try again.', 'danger')
    
    return render_template('register.html', title='Register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        # Validate input
        if not email or not password:
            flash('Email and password are required!', 'danger')
            return render_template('login.html', title='Login')
        
        # Check user credentials
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'danger')
    
    return render_template('login.html', title='Login')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's recommendations
    recommendations = Recommendation.query.filter_by(user_id=current_user.id).order_by(Recommendation.score.desc()).all()
    
    # Convert recommendations to dictionaries for easier template rendering
    recommendation_data = []
    for rec in recommendations:
        career = Career.query.get(rec.career_id)
        market_trend = MarketTrend.query.filter_by(career_id=career.id).order_by(MarketTrend.updated_at.desc()).first()
        
        recommendation_data.append({
            'id': rec.id,
            'career': career,
            'score': rec.score,
            'date_time': rec.date_time,
            'market_trend': market_trend
        })
    
    # Check if user has completed profile
    profile_completed = current_user.has_completed_profile()
    
    return render_template(
        'dashboard.html', 
        title='Dashboard',
        recommendations=recommendation_data,
        profile_completed=profile_completed
    )

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        skills = request.form.getlist('skills')
        education_level = request.form.get('education_level')
        education_field = request.form.get('education_field')
        education_institution = request.form.get('education_institution')
        experience_years = request.form.get('experience_years')
        experience_roles = request.form.getlist('experience_roles')
        interests = request.form.getlist('interests')
        
        # Update user profile
        current_user.name = name
        current_user.age = int(age) if age else None
        current_user.set_skills(skills)
        
        # Update education
        education = {
            'level': education_level,
            'field': education_field,
            'institution': education_institution
        }
        current_user.set_education([education])
        
        # Update experience
        experience = {
            'years': experience_years,
            'roles': experience_roles
        }
        current_user.set_experience([experience])
        
        # Update interests
        current_user.set_interests(interests)
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating profile: {e}")
            flash('An error occurred. Please try again.', 'danger')
    
    # For GET request, prepare data for form
    user_skills = current_user.get_skills()
    user_education = current_user.get_education()[0] if current_user.get_education() else {}
    user_experience = current_user.get_experience()[0] if current_user.get_experience() else {}
    user_interests = current_user.get_interests()
    
    return render_template(
        'profile.html', 
        title='Profile',
        user=current_user,
        skills=user_skills,
        education=user_education,
        experience=user_experience,
        interests=user_interests
    )

@app.route('/assessment')
@login_required
def assessment():
    # Check if user has completed profile
    if not current_user.has_completed_profile():
        flash('Please complete your profile before taking the assessment.', 'warning')
        return redirect(url_for('profile'))
    
    return render_template('assessment.html', title='Career Assessment')

@app.route('/process_assessment', methods=['POST'])
@login_required
def process_assessment():
    try:
        # Get additional assessment data from form
        additional_skills = request.form.getlist('additional_skills')
        preferred_industries = request.form.getlist('preferred_industries')
        work_values = request.form.getlist('work_values')
        
        # Merge with user profile data
        user_data = {
            'id': current_user.id,
            'name': current_user.name,
            'skills': current_user.get_skills() + additional_skills,
            'education': current_user.get_education(),
            'experience': current_user.get_experience(),
            'interests': current_user.get_interests() + preferred_industries + work_values
        }
        
        # Get all careers and market trends
        careers = Career.query.all()
        careers_data = []
        
        for career in careers:
            careers_data.append({
                'id': career.id,
                'name': career.name,
                'description': career.description,
                'required_skills': career.get_required_skills(),
                'industry': career.industry
            })
        
        market_trends = MarketTrend.query.all()
        trends_data = []
        
        for trend in market_trends:
            trends_data.append({
                'career_id': trend.career_id,
                'demand_level': trend.demand_level,
                'salary_range': trend.salary_range
            })
        
        # Generate recommendations
        recommendations = recommendation_engine.generate_career_recommendations(
            user_data, 
            careers_data, 
            trends_data
        )
        
        # Save recommendations to database
        for rec in recommendations:
            # Check if recommendation already exists
            existing_rec = Recommendation.query.filter_by(
                user_id=current_user.id,
                career_id=rec['career']['id']
            ).first()
            
            if existing_rec:
                # Update existing recommendation
                existing_rec.score = rec['score']
                existing_rec.date_time = datetime.utcnow()
            else:
                # Create new recommendation
                new_rec = Recommendation(
                    user_id=current_user.id,
                    career_id=rec['career']['id'],
                    score=rec['score']
                )
                db.session.add(new_rec)
        
        db.session.commit()
        flash('Assessment completed! View your career recommendations below.', 'success')
        return redirect(url_for('recommendations'))
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing assessment: {e}")
        flash('An error occurred while processing your assessment. Please try again.', 'danger')
        return redirect(url_for('assessment'))

@app.route('/recommendations')
@login_required
def recommendations():
    # Get user's recommendations
    recommendations = Recommendation.query.filter_by(user_id=current_user.id).order_by(Recommendation.score.desc()).all()
    
    if not recommendations:
        flash('No recommendations found. Please complete the assessment first.', 'info')
        return redirect(url_for('assessment'))
    
    # Convert recommendations to dictionaries for easier template rendering
    recommendation_data = []
    for rec in recommendations:
        career = Career.query.get(rec.career_id)
        market_trend = MarketTrend.query.filter_by(career_id=career.id).order_by(MarketTrend.updated_at.desc()).first()
        
        recommendation_data.append({
            'id': rec.id,
            'career': career,
            'score': rec.score,
            'date_time': rec.date_time,
            'market_trend': market_trend
        })
    
    return render_template(
        'recommendations.html', 
        title='Career Recommendations',
        recommendations=recommendation_data
    )

@app.route('/career/<int:career_id>')
@login_required
def career_details(career_id):
    career = Career.query.get_or_404(career_id)
    market_trend = MarketTrend.query.filter_by(career_id=career.id).order_by(MarketTrend.updated_at.desc()).first()
    
    # Get recommendation if exists
    recommendation = Recommendation.query.filter_by(
        user_id=current_user.id,
        career_id=career.id
    ).first()
    
    # Get user feedback if exists
    feedback = None
    if recommendation:
        feedback = Feedback.query.filter_by(
            user_id=current_user.id,
            recommendation_id=recommendation.id
        ).first()
    
    return render_template(
        'career_details.html',
        title=f'Career: {career.name}',
        career=career,
        market_trend=market_trend,
        recommendation=recommendation,
        feedback=feedback
    )

@app.route('/market_trends')
@login_required
def market_trends():
    trends = MarketTrend.query.join(Career).all()
    
    trend_data = []
    for trend in trends:
        career = Career.query.get(trend.career_id)
        trend_data.append({
            'id': trend.id,
            'career': career,
            'demand_level': trend.demand_level,
            'salary_range': trend.salary_range,
            'updated_at': trend.updated_at
        })
    
    return render_template(
        'market_trends.html',
        title='Market Trends',
        trends=trend_data
    )

@app.route('/submit_feedback', methods=['POST'])
@login_required
def submit_feedback():
    recommendation_id = request.form.get('recommendation_id')
    rating = request.form.get('rating')
    comments = request.form.get('comments')
    
    if not recommendation_id or not rating:
        flash('Rating is required!', 'danger')
        return redirect(url_for('recommendations'))
    
    # Check if recommendation exists and belongs to current user
    recommendation = Recommendation.query.filter_by(
        id=recommendation_id,
        user_id=current_user.id
    ).first()
    
    if not recommendation:
        flash('Invalid recommendation!', 'danger')
        return redirect(url_for('recommendations'))
    
    # Check if feedback already exists
    existing_feedback = Feedback.query.filter_by(
        user_id=current_user.id,
        recommendation_id=recommendation_id
    ).first()
    
    try:
        if existing_feedback:
            # Update existing feedback
            existing_feedback.rating = int(rating)
            existing_feedback.comments = comments
        else:
            # Create new feedback
            new_feedback = Feedback(
                user_id=current_user.id,
                recommendation_id=recommendation_id,
                rating=int(rating),
                comments=comments
            )
            db.session.add(new_feedback)
        
        db.session.commit()
        flash('Feedback submitted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting feedback: {e}")
        flash('An error occurred. Please try again.', 'danger')
    
    # Redirect back to the page where feedback was submitted from
    return redirect(request.referrer or url_for('recommendations'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', title='Not Found', error=error), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', title='Server Error', error=error), 500

# Add seed data for initial setup
@app.route('/seed_data', methods=['GET'])
def seed_data():
    if not app.debug:
        return jsonify({'error': 'This route is only available in debug mode'}), 403
    
    try:
        # Create AI Model
        if not AIModel.query.first():
            ai_model = AIModel(
                name='Career Recommendation Model',
                algorithm='TF-IDF + Cosine Similarity',
                accuracy=0.85
            )
            db.session.add(ai_model)
        
        # Create careers if they don't exist
        if not Career.query.first():
            careers_data = [
                {
                    'name': 'Software Engineer',
                    'description': 'Design, develop, and maintain software systems and applications.',
                    'required_skills': json.dumps(['Python', 'JavaScript', 'SQL', 'Problem Solving', 'Algorithm Design']),
                    'industry': 'Information Technology'
                },
                {
                    'name': 'Data Scientist',
                    'description': 'Analyze and interpret complex data to assist in decision-making and strategy development.',
                    'required_skills': json.dumps(['Python', 'Statistics', 'Machine Learning', 'Data Visualization', 'SQL']),
                    'industry': 'Information Technology'
                },
                {
                    'name': 'Digital Marketing Specialist',
                    'description': 'Develop and implement digital marketing strategies to promote products or services.',
                    'required_skills': json.dumps(['SEO', 'Content Marketing', 'Social Media Marketing', 'Analytics', 'Copywriting']),
                    'industry': 'Marketing'
                },
                {
                    'name': 'Financial Analyst',
                    'description': 'Analyze financial data and provide insights to help businesses make decisions.',
                    'required_skills': json.dumps(['Financial Modeling', 'Excel', 'Data Analysis', 'Accounting', 'Business Intelligence']),
                    'industry': 'Finance'
                },
                {
                    'name': 'UX/UI Designer',
                    'description': 'Design user interfaces and experiences for websites and applications.',
                    'required_skills': json.dumps(['UI Design', 'Wireframing', 'Prototyping', 'User Research', 'Adobe XD']),
                    'industry': 'Design'
                }
            ]
            
            for career_data in careers_data:
                career = Career(**career_data)
                db.session.add(career)
        
        # Create market trends if they don't exist
        if not MarketTrend.query.first():
            # First get careers
            careers = Career.query.all()
            
            for career in careers:
                # Create market trend for each career
                if career.name == 'Software Engineer':
                    demand_level = 0.9
                    salary_range = '70000-120000'
                elif career.name == 'Data Scientist':
                    demand_level = 0.85
                    salary_range = '80000-130000'
                elif career.name == 'Digital Marketing Specialist':
                    demand_level = 0.75
                    salary_range = '50000-90000'
                elif career.name == 'Financial Analyst':
                    demand_level = 0.7
                    salary_range = '60000-100000'
                elif career.name == 'UX/UI Designer':
                    demand_level = 0.8
                    salary_range = '65000-110000'
                else:
                    demand_level = 0.5
                    salary_range = '50000-80000'
                
                market_trend = MarketTrend(
                    career_id=career.id,
                    demand_level=demand_level,
                    salary_range=salary_range
                )
                db.session.add(market_trend)
        
        db.session.commit()
        return jsonify({'message': 'Seed data created successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error seeding data: {e}")
        return jsonify({'error': str(e)}), 500
