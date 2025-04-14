
from app import db

def reset_db_session():
    """Reset the database session to recover from transaction errors"""
    try:
        db.session.rollback()
        return True
    except Exception as e:
        print(f"Error resetting DB session: {str(e)}")
        return False
