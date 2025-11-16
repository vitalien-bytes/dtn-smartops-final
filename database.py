import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Récupérer l’URL de connexion
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL n'est pas défini dans Render.")

# Création du moteur SQLAlchemy pour Aiven (pg8000)
engine = create_engine(
    DATABASE_URL,
    connect_args={"ssl": True},   # SSL obligatoire pour Aiven
    pool_pre_ping=True
)

# Session DB
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base de modèles
Base = declarative_base()
