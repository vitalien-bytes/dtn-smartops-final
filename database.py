import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1) On récupère l'URL depuis Render / Aiven
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("❌ La variable d'environnement DATABASE_URL est manquante")

# 2) Render / Aiven donnent un schéma "postgres://"
#    On le convertit pour utiliser le driver pg8000
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+pg8000://", 1)

# 3) Aiven ajoute ?sslmode=require, que pg8000 ne supporte pas
#    On le remplace par ?ssl=true (paramètre accepté par pg8000)
DATABASE_URL = DATABASE_URL.replace("?sslmode=require", "?ssl=true")

# 4) Création du moteur SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

# 5) Session + Base
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
