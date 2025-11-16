import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# -----------------------------------------------------
# 1) Lire DATABASE_URL depuis Render
# -----------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("❌ DATABASE_URL manquant !")

# -----------------------------------------------------
# 2) Convertir postgres:// --> postgresql+pg8000://
# -----------------------------------------------------
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+pg8000://")

# -----------------------------------------------------
# 3) Créer l'engine (SANS sslmode, SANS connect_args)
# -----------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

# -----------------------------------------------------
# 4) Sessions SQLAlchemy
# -----------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
