
from app import app, db
from models import Site, SitePage

def migrate_pixi_spaces():
    """
    This script checks if the database has pixi site type support.
    It doesn't change any existing data, just ensures compatibility.
    """
    with app.app_context():
        # Check for site_type column having pixi as a value
        try:
            print("Checking for Pixi space support in database...")
            # Just testing a simple query that would fail if the schema wasn't compatible
            db.session.query(Site).filter(Site.site_type == 'pixi').first()
            print("Database is compatible with Pixi spaces.")
        except Exception as e:
            print(f"Database error: {str(e)}")
            print("Please make sure your database schema is up to date.")
            return False
            
        return True

if __name__ == "__main__":
    success = migrate_pixi_spaces()
    if success:
        print("Migration completed successfully.")
    else:
        print("Migration failed. Please check the database schema.")
