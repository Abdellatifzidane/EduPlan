from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# SQLite configuration - le fichier sera créé dans le dossier data/
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/eduplan.db")

# Configuration spécifique pour SQLite
engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency pour obtenir une session de base de données"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialiser la base de données"""
    from .models import Base
    Base.metadata.create_all(bind=engine)
