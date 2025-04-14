
from app import app, db
from models import Site, User
import sys

def repair_site_types():
    """Fix site types in the database"""
    print("Repairing site types in the database...")
    try:
        with app.app_context():
            # Update any null site_type values to 'web'
            count = db.session.execute(db.text("UPDATE site SET site_type = 'web' WHERE site_type IS NULL OR site_type = ''")).rowcount
            db.session.commit()
            
            # Ensure all Python sites are properly marked
            python_sites = db.session.execute(db.text("SELECT COUNT(*) FROM site WHERE python_content IS NOT NULL AND python_content != '' AND site_type != 'python'")).scalar()
            if python_sites > 0:
                db.session.execute(db.text("UPDATE site SET site_type = 'python' WHERE python_content IS NOT NULL AND python_content != '' AND site_type != 'python'"))
                db.session.commit()
            
            # Count sites by type
            web_count = db.session.execute(db.text("SELECT COUNT(*) FROM site WHERE site_type = 'web'")).scalar()
            python_count = db.session.execute(db.text("SELECT COUNT(*) FROM site WHERE site_type = 'python'")).scalar()
            
            print(f"Site types fixed: {count} rows updated")
            print(f"Current site counts: {web_count} web sites, {python_count} python sites")
            print("Repair completed successfully")
            return True
    except Exception as e:
        print(f"Error repairing site types: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "repair_site_types":
        repair_site_types()
    else:
        print("Usage: python db_utils.py repair_site_types")
