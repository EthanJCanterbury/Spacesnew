
import os
from app import app, db
from models import GalleryEntry

def update_gallery_table():
    """Updates the gallery table by dropping and recreating it."""
    with app.app_context():
        print("Updating gallery table...")
        
        # Create a SQL command to drop the column if it exists
        db_command = """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name='gallery_entry' AND column_name='category'
            ) THEN
                ALTER TABLE gallery_entry DROP COLUMN category;
            END IF;
        END $$;
        """
        
        # Execute the command
        db.session.execute(db_command)
        db.session.commit()
        
        print("Gallery table updated successfully.")

if __name__ == "__main__":
    update_gallery_table()
