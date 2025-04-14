import os
from app import app, db
from models import GalleryEntry

def fix_gallery_table():
    """Add the missing category column to the gallery_entry table."""
    print("Fixing gallery table...")

    try:
        with app.app_context():
            # Execute SQL to add the missing column if it doesn't exist
            db.session.execute(db.text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'gallery_entry' AND column_name = 'category'
                    ) THEN
                        ALTER TABLE gallery_entry ADD COLUMN category VARCHAR(50);
                    END IF;
                END
                $$;
            """))
            db.session.commit()
            print("Gallery table fixed successfully.")
            return True
    except Exception as e:
        print(f"Error fixing gallery table: {str(e)}")
        return False

if __name__ == "__main__":
    fix_gallery_table()