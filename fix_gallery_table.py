
import os
from db_command import run_db_command

def fix_gallery_table():
    """Fix the gallery_entry table by adding missing columns."""
    print("Fixing gallery table...")
    
    sql_command = """
    DO $$
    BEGIN
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
        
        -- Remove category column if it exists
        IF EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name='gallery_entry' AND column_name='category'
        ) THEN
            ALTER TABLE gallery_entry DROP COLUMN category;
        END IF;
    END $$;
    """
    
    run_db_command(sql_command)
    print("Gallery table fixed successfully.")

if __name__ == "__main__":
    fix_gallery_table()
