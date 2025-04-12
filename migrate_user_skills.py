"""
Migration script to update User model with skills relationship.
"""
import logging
from app import app, db
from models import User, Skill
from sqlalchemy import text, Column, String, inspect
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_user_skills():
    """Migrate user skills from text field to relationship."""
    with app.app_context():
        try:
            # First, ensure the user_skill association table exists
            inspector = inspect(db.engine)
            if 'user_skill' not in inspector.get_table_names():
                logger.info("Creating user_skill table...")
                db.session.execute(text('''
                    CREATE TABLE IF NOT EXISTS user_skill (
                        user_id INTEGER NOT NULL REFERENCES "user"(id),
                        skill_id INTEGER NOT NULL REFERENCES skill(id),
                        PRIMARY KEY (user_id, skill_id)
                    )
                '''))
                logger.info("user_skill table created successfully")
            else:
                logger.info("user_skill table already exists")
                
            # Get existing users with their skills as text
            users_result = db.session.execute(text('SELECT id, username, skills FROM "user"'))
            users_data = [dict(row._mapping) for row in users_result]
            
            logger.info(f"Found {len(users_data)} users to migrate")
            
            # Add skills_text column if needed
            try:
                db.session.execute(text('ALTER TABLE "user" ADD COLUMN skills_text TEXT'))
                logger.info("Added skills_text column to user table")
            except ProgrammingError:
                # Column might already exist
                logger.info("skills_text column already exists")
                db.session.rollback()
            
            # Update users with skills from text to relationship
            for user_data in users_data:
                user_id = user_data['id']
                username = user_data['username']
                skills_text = user_data.get('skills', '')
                
                logger.info(f"Migrating skills for user {user_id} - {username}")
                
                # Update skills_text column
                if skills_text:
                    db.session.execute(
                        text('UPDATE "user" SET skills_text = :skills_text WHERE id = :user_id'),
                        {"skills_text": skills_text, "user_id": user_id}
                    )
                
                # Convert text to relationships
                if skills_text:
                    # Get skill names from text
                    skill_names = [name.strip() for name in skills_text.split(',') if name.strip()]
                    logger.info(f"Found {len(skill_names)} skills in text: {skill_names}")
                    
                    # Find skills in database and create relationships
                    for skill_name in skill_names:
                        skill_result = db.session.execute(
                            text('SELECT id FROM skill WHERE name = :name'),
                            {"name": skill_name}
                        ).fetchone()
                        
                        if skill_result:
                            skill_id = skill_result[0]
                            
                            # Check if relationship already exists
                            existing = db.session.execute(
                                text('SELECT 1 FROM user_skill WHERE user_id = :user_id AND skill_id = :skill_id'),
                                {"user_id": user_id, "skill_id": skill_id}
                            ).fetchone()
                            
                            if not existing:
                                # Add relationship
                                db.session.execute(
                                    text('INSERT INTO user_skill (user_id, skill_id) VALUES (:user_id, :skill_id)'),
                                    {"user_id": user_id, "skill_id": skill_id}
                                )
                                logger.info(f"Added skill {skill_name} to user {username}")
            
            # Commit changes
            db.session.commit()
            logger.info("Migration completed successfully")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during migration: {e}")
            raise

if __name__ == "__main__":
    migrate_user_skills()