# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base  # Import Base from models

# Use the updated SQLALCHEMY_DATABASE_URI with pg8000
SQLALCHEMY_DATABASE_URI = "postgresql+pg8000://postgres:B.ikram0@localhost/BDD"

# Create the SQLAlchemy engine to connect to the database
engine = create_engine(SQLALCHEMY_DATABASE_URI)

# Create the session maker to interact with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the tables in the database (if they don't exist already)
Base.metadata.create_all(bind=engine)
