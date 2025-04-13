
from app import app, db
from sqlalchemy import text
from models import User

def add_club_leader_role_column():
    """Add is_club_leader_role column to user table if it doesn't exist"""
    with app.app_context():
        print("Checking if is_club_leader_role column exists in user table...")
        
        try:
            # Check if column exists
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'user' AND column_name = 'is_club_leader_role'
            """))
            
            if result.fetchone() is None:
                print("Adding is_club_leader_role column to user table...")
                db.session.execute(text("""
                    ALTER TABLE "user" ADD COLUMN is_club_leader_role BOOLEAN DEFAULT FALSE
                """))
                
                # Set is_club_leader_role to true for existing club leaders
                club_leaders = db.session.execute(text("""
                    SELECT DISTINCT leader_id FROM club
                """)).fetchall()
                
                for row in club_leaders:
                    user_id = row[0]
                    db.session.execute(text("""
                        UPDATE "user" SET is_club_leader_role = TRUE WHERE id = :user_id
                    """), {"user_id": user_id})
                
                db.session.commit()
                print("Successfully added is_club_leader_role column and migrated data")
            else:
                print("is_club_leader_role column already exists")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error adding is_club_leader_role column: {str(e)}")

if __name__ == "__main__":
    add_club_leader_role_column()
