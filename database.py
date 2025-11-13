import os
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Récupère l'URL depuis Render (Environment -> DATABASE_URL)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL n'est pas définie dans les variables d'environnement.")

# 2. Adapter le schéma Aiven : postgres:// -> postgresql+pg8000://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql+pg8000://",
        1  # seulement la première occurrence
    )

# 3. Supprimer le paramètre sslmode=require (pg8000 ne le supporte pas)
if "sslmode=" in DATABASE_URL:
    # enlève ?sslmode=... ou &sslmode=...
    DATABASE_URL = re.sub(r"[?&]sslmode=[^&]+", "", DATABASE_URL)

    # Si l'URL finit par ? ou &, on nettoie
    if DATABASE_URL.endswith("?") or DATABASE_URL.endswith("&"):
        DATABASE_URL = DATABASE_URL[:-1]

# 4. Créer le moteur SQLAlchemy
engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()
