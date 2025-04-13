
from app import app, db
from sqlalchemy import text
from models import Club, ClubMembership, ClubPost, ClubResource, ClubChatChannel, ClubChatMessage

def fix_database():
    """Fix database schema issues by adding missing columns."""
    with app.app_context():
        print("Starting database schema fixes...")
        db.session.commit()  # Reset any pending transaction

        # Fix club_post table - add user_id column if missing
        try:
            print("Checking club_post table...")
            db.session.execute(text("""
                DO $$ 
                BEGIN
                    BEGIN
                        ALTER TABLE club_post ADD COLUMN user_id INTEGER REFERENCES "user"(id);
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                END $$;
            """))
            db.session.commit()
            print("✅ Fixed club_post table")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error fixing club_post table: {str(e)}")

        # Fix club_resource table - add created_by column if missing
        try:
            print("Checking club_resource table...")
            db.session.execute(text("""
                DO $$ 
                BEGIN
                    BEGIN
                        ALTER TABLE club_resource ADD COLUMN created_by INTEGER REFERENCES "user"(id);
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                END $$;
            """))
            db.session.commit()
            print("✅ Fixed club_resource table")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error fixing club_resource table: {str(e)}")

        # Fix club_assignment table - add created_by column if missing
        try:
            print("Checking club_assignment table...")
            db.session.execute(text("""
                DO $$ 
                BEGIN
                    BEGIN
                        ALTER TABLE club_assignment ADD COLUMN created_by INTEGER REFERENCES "user"(id);
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                END $$;
            """))
            db.session.commit()
            print("✅ Fixed club_assignment table")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error fixing club_assignment table: {str(e)}")

        print("Database schema fixes completed.")

if __name__ == "__main__":
    fix_database()
