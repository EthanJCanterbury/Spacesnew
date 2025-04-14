
from app import db
from models import User, Site

def reset_db_session():
    """Reset the database session to recover from transaction errors"""
    try:
        db.session.rollback()
        return True
    except Exception as e:
        print(f"Error resetting DB session: {str(e)}")
        return False

def get_user_sites(user_id):
    """Get all sites for a specific user"""
    try:
        sites = Site.query.filter_by(user_id=user_id).all()
        return sites
    except Exception as e:
        print(f"Error getting user sites: {str(e)}")
        reset_db_session()
        return []
