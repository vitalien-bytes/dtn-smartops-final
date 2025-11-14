# database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# -----------------------------------------------------------------------------
# 1) Récupération de l'URL de connexion
# -----------------------------------------------------------------------------
# Le nom que nous avions défini était : DATABASE_URL
# Exemple Aiven / ElephantSQL : 
# postgresql://user:password@host:port/dbname
# -----------------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError(
        "❌ La variable d'environnement DATABASE_URL n'est pas définie. "
        "Pense à la mettre dans ton .env"
    )

# -----------------------------------------------------------------------------
# 2) Création du moteur SQLAlchemy
# -----------------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

# -----------------------------------------------------------------------------
# 3) Création de la Session locale
# -----------------------------------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# -----------------------------------------------------------------------------
# 4) Base déclarative (modèles)
# -----------------------------------------------------------------------------
Base = declarative_base()

# -----------------------------------------------------------------------------
# 5) Dépendance FastAPI pour obtenir une session DB
# -----------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
