from app import app, db
from sqlalchemy import text
from models import User, Site, SitePage, UserActivity, Club, ClubMembership
from models import ClubPost, ClubAssignment, ClubResource

def setup_database():
    """Create all database tables if they don't exist."""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully.")

        # Setup complete

                    db.session.commit()
                print(f"Setup complete for club: {club.name}")

        print("Database setup complete.")

if __name__ == "__main__":
    setup_database()