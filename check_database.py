import logging
from app import app, db
from models import User, Skill, Career, MarketTrend, Assessment, Recommendation
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database_content():
    """Check the contents of the database"""
    # Use raw SQL for table counts to avoid model mapping issues
    def get_count(table_name):
        result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        return result.scalar()
    
    # Check users
    user_count = get_count("user")
    logger.info(f"Users: {user_count}")
    if user_count > 0:
        users = User.query.limit(5).all()
        for user in users:  # Show only the first 5
            logger.info(f"  - {user.username} ({user.email})")
        if user_count > 5:
            logger.info(f"  ... and {user_count - 5} more")
    
    # Check skills
    skill_count = get_count("skill")
    logger.info(f"Skills: {skill_count}")
    if skill_count > 0:
        skills = Skill.query.limit(5).all()
        for skill in skills:  # Show only the first 5
            logger.info(f"  - {skill.name}")
        if skill_count > 5:
            logger.info(f"  ... and {skill_count - 5} more")
    
    # Check careers
    career_count = get_count("career")
    logger.info(f"Careers: {career_count}")
    if career_count > 0:
        # Use raw SQL to get career data
        result = db.session.execute(text("SELECT id, name FROM career LIMIT 5"))
        for row in result:
            # Count skills for this career
            skill_count = db.session.execute(
                text(f"SELECT COUNT(*) FROM career_skill WHERE career_id = {row.id}")
            ).scalar()
            logger.info(f"  - {row.name} (Skills: {skill_count})")
        if career_count > 5:
            logger.info(f"  ... and {career_count - 5} more")
    
    # Check market trends
    trend_count = get_count("market_trend")
    logger.info(f"Market Trends: {trend_count}")
    
    # Check assessments
    assessment_count = get_count("assessment")
    logger.info(f"Assessments: {assessment_count}")
    
    # Check recommendations
    recommendation_count = get_count("recommendation")
    logger.info(f"Recommendations: {recommendation_count}")
    
    # Check career_skill associations
    career_skill_count = db.session.execute(text("SELECT COUNT(*) FROM career_skill")).scalar()
    logger.info(f"Career-Skill Associations: {career_skill_count}")

if __name__ == "__main__":
    logger.info("Checking database content...")
    
    with app.app_context():
        check_database_content()