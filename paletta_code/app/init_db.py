from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from .models import Category

def init_db():
    # Create all tables
    Base.metadata.create_all(bind=engine)

def seed_categories(db: Session):
    # Predefined categories
    categories = [
        {"name": "Buildings", "description": "Architecture and structural designs"},
        {"name": "Humanities", "description": "Arts, literature, and cultural content"},
        {"name": "People", "description": "Portraits and human interactions"},
        {"name": "Science", "description": "Scientific experiments and discoveries"},
        {"name": "Transports", "description": "Vehicles and transportation systems"}
    ]

    # Check if categories already exist
    existing_categories = db.query(Category).all()
    if existing_categories:
        print("Categories already exist in the database")
        return

    # Add categories to database
    for category_data in categories:
        category = Category(**category_data)
        db.add(category)
    
    try:
        db.commit()
        print("Categories successfully added to database")
    except Exception as e:
        print(f"Error adding categories: {e}")
        db.rollback()

def main():
    # Initialize database
    init_db()
    
    # Get database session
    db = next(get_db())
    
    try:
        # Seed categories
        seed_categories(db)
    finally:
        db.close()

if __name__ == "__main__":
    main() 