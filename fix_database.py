
from app import app, db
from sqlalchemy import text
from models import Club, ClubMembership, ClubPost, ClubResource, ClubChatChannel, ClubChatMessage

def fix_database():
    """Fix database schema issues by adding missing columns."""
    with app.app_context():
        print("Starting database schema fixes...")
        db.session.commit()  # Reset any pending transaction

        # Fix club_post table - handle column issues
        try:
            print("Checking club_post table...")
            # Check if author_id column exists and rename it to user_id if needed
            db.session.execute(text("""
                DO $$ 
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'club_post' AND column_name = 'author_id'
                    ) THEN
                        ALTER TABLE club_post RENAME COLUMN author_id TO user_id;
                    END IF;
                    
                    -- Add user_id column if it doesn't exist
                    BEGIN
                        ALTER TABLE club_post ADD COLUMN user_id INTEGER REFERENCES "user"(id);
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                    
                    -- Make sure there's no NOT NULL constraint on the column if we just added it
                    ALTER TABLE club_post ALTER COLUMN user_id DROP NOT NULL;
                END $$;
            """))
            db.session.commit()
            print("✅ Fixed club_post table")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error fixing club_post table: {str(e)}")

        # Fix club_resource table - handle column issues
        try:
            print("Checking club_resource table...")
            # Check if creator_id column exists and rename it to created_by if needed
            db.session.execute(text("""
                DO $$ 
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'club_resource' AND column_name = 'creator_id'
                    ) THEN
                        ALTER TABLE club_resource RENAME COLUMN creator_id TO created_by;
                    END IF;
                    
                    -- Add created_by column if it doesn't exist
                    BEGIN
                        ALTER TABLE club_resource ADD COLUMN created_by INTEGER REFERENCES "user"(id);
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                    
                    -- Make sure there's no NOT NULL constraint on the column if we just added it
                    ALTER TABLE club_resource ALTER COLUMN created_by DROP NOT NULL;
                END $$;
            """))
            db.session.commit()
            print("✅ Fixed club_resource table")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error fixing club_resource table: {str(e)}")

        # Fix club_assignment table - add is_active and created_by columns if missing
        try:
            print("Checking club_assignment table...")
            db.session.execute(text("""
                DO $$ 
                BEGIN
                    -- Add created_by column if it doesn't exist
                    BEGIN
                        ALTER TABLE club_assignment ADD COLUMN created_by INTEGER REFERENCES "user"(id);
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                    
                    -- Add is_active column if it doesn't exist
                    BEGIN
                        ALTER TABLE club_assignment ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                    
                    -- Make sure there's no NOT NULL constraint on the columns if we just added them
                    ALTER TABLE club_assignment ALTER COLUMN created_by DROP NOT NULL;
                END $$;
            """))
            db.session.commit()
            print("✅ Fixed club_assignment table")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error fixing club_assignment table: {str(e)}")

        # Update club_chat_message table to fix channel_id constraints
        try:
            print("Checking club_chat_message table...")
            db.session.execute(text("""
                DO $$ 
                BEGIN
                    -- Remove NOT NULL constraint from channel_id if it exists
                    BEGIN
                        ALTER TABLE club_chat_message ALTER COLUMN channel_id DROP NOT NULL;
                    EXCEPTION
                        WHEN undefined_column THEN NULL;
                        WHEN undefined_object THEN NULL;
                    END;
                END $$;
            """))
            db.session.commit()
            print("✅ Fixed club_chat_message table")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error fixing club_chat_message table: {str(e)}")

        print("Database schema fixes completed.")

if __name__ == "__main__":
    fix_database()
