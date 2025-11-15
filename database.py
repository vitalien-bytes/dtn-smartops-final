import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

# Forcer l'utilisation de pg8000 si Render fournit un URL "postgresql://"
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+pg8000://")

# IMPORTANT : pg8000 ne supporte PAS 'sslmode' dans connect_args
# Render impose SSL, mais pg8000 gère le SSL automatiquement via l’URL
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
