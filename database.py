from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# On récupère la variable d'environnement Render
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL non défini dans les variables Render.")

# Crée le moteur SQLAlchemy
engine = create_engine(DATABASE_URL)

# Crée une session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base commune
Base = declarative_base()
