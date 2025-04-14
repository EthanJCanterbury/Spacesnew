
import os
from app import app, db
from sqlalchemy import text
from models import GalleryEntry

def update_gallery_table():
    """Updates the gallery table by adding necessary columns."""
    with app.app_context():
        print("Updating gallery table...")
        
        # Create a SQL command to add columns if they don't exist
        db_command = text("""
        DO $$
        BEGIN
            -- Remove category column if it exists
            IF EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name='gallery_entry' AND column_name='category'
            ) THEN
                ALTER TABLE gallery_entry DROP COLUMN category;
            END IF;
            
            -- Add created_at column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name='gallery_entry' AND column_name='created_at'
            ) THEN
                ALTER TABLE gallery_entry ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
            END IF;
            
            -- Add updated_at column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name='gallery_entry' AND column_name='updated_at'
            ) THEN
                ALTER TABLE gallery_entry ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
            END IF;
        END $$;
        """)
        
        # Execute the command
        db.session.execute(db_command)
        db.session.commit()
        
        print("Gallery table updated successfully.")

if __name__ == "__main__":
    update_gallery_table()
