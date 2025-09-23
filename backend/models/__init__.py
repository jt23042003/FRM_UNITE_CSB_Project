from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Shared database configuration
DATABASE_URL = "postgresql://unitedb_user:password123@34.47.219.225:5432/unitedb"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import all models to ensure they are registered with the Base
from .case_main import CaseMain
from .assignment import Assignment
from .case_history import CaseHistory
from .user_table import UserTable

# Create all tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
