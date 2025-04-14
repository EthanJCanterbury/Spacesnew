
from app import app, db
from models import User, Site
import sys

def fix_spaces_dropdown():
    """Utility script to fix spaces dropdown by ensuring all site types are properly set"""
    print("Fixing spaces dropdown...")
    try:
        with app.app_context():
            # Update any null site_type values to 'web'
            db.session.execute(db.text("UPDATE site SET site_type = 'web' WHERE site_type IS NULL"))
            db.session.commit()
            
            # Count sites with proper types
            web_count = db.session.execute(db.text("SELECT COUNT(*) FROM site WHERE site_type = 'web'")).scalar()
            python_count = db.session.execute(db.text("SELECT COUNT(*) FROM site WHERE site_type = 'python'")).scalar()
            
            print(f"Updated site types: {web_count} web sites, {python_count} python sites")
            print("Spaces dropdown should now display correctly")
        print("Fix completed successfully")
        return True
    except Exception as e:
        print(f"Error fixing spaces dropdown: {str(e)}")
        return False

if __name__ == "__main__":
    fix_spaces_dropdown()
