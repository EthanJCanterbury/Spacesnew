
import os
from app import app, db
from models import GalleryEntry

def create_gallery_table():
    """Create the gallery table if it doesn't exist."""
    with app.app_context():
        print("Creating gallery table...")
        db.create_all()
        print("Gallery table created successfully.")

if __name__ == "__main__":
    create_gallery_table()
