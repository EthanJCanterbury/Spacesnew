
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

def repair_gallery_entries():
    """Repair gallery entries with missing category information"""
    try:
        from app import db
        from models import GalleryEntry
        
        # Add the category column if missing
        db.session.execute(db.text("""
            DO $$
            BEGIN

def ensure_gallery_likes_table():
    """Ensure the gallery_entry_like table exists"""
    try:
        from app import db
        
        # Create the gallery_entry_like table if it doesn't exist
        db.session.execute(db.text("""
            CREATE TABLE IF NOT EXISTS gallery_entry_like (
                id SERIAL PRIMARY KEY,
                entry_id INTEGER NOT NULL REFERENCES gallery_entry(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                UNIQUE(entry_id, user_id)
            )
        """))
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error ensuring gallery likes table: {str(e)}")
        return False

                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'gallery_entry' AND column_name = 'category'
                ) THEN
                    ALTER TABLE gallery_entry ADD COLUMN category VARCHAR(50);
                END IF;
            END
            $$;
        """))
        
        # Set default category for entries with NULL category
        db.session.execute(db.text("UPDATE gallery_entry SET category = 'other' WHERE category IS NULL"))
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error repairing gallery entries: {str(e)}")
        reset_db_session()
        return False
