# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ------------------------------------------------------------------
# 1) Récupération de l’URL de connexion
# ------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "❌ La variable d'environnement DATABASE_URL n'est pas définie."
        " Va dans Render → Environment et colle l'URL Aiven."
    )

# Aiven donne un URL en postgres:// … → on le normalise pour SQLAlchemy
# et on laisse psycopg2 gérer ?sslmode=require
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    # Exemple final :
    # postgresql://avnadmin:motdepasse@host:12779/defaultdb?sslmode=require

# ------------------------------------------------------------------
# 2) Création du moteur SQLAlchemy
#    (on ne passe plus de ssl / sslmode dans connect_args,
#     c’est psycopg2 qui gère tout via l’URL)
# ------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

# ------------------------------------------------------------------
# 3) Session et Base
# ------------------------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()
