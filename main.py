import os, secrets
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, Board, Column, Card

# --- Création automatique des tables ---
Base.metadata.create_all(bind=engine)

# --- Initialisation de l'application ---
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=secrets.token_hex(16))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Variables d'environnement ---
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "DTN-2025-secure-base")
BOARD_TITLE = os.getenv("BOARD_TITLE", "DTN SmartOps")

# --- Connexion à la base ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Page de connexion ---
@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# --- Traitement du login ---
@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        request.session["logged_in"] = True
        return RedirectResponse("/board", status_code=302)
    raise HTTPException(status_code=401, detail="Identifiants invalides")

# --- Tableau principal ---
@app.get("/board", response_class=HTMLResponse)
def board_page(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logged_in"):
        return RedirectResponse("/", status_code=302)

    board = db.query(Board).first()
    if not board:
        board = Board(title=BOARD_TITLE)
        db.add(board)
        db.commit()
        db.refresh(board)

    columns = db.query(Column).filter(Column.board_id == board.id).all()
    return templates.TemplateResponse(
        "board.html",
        {"request": request, "board": board, "columns": columns},
    )

# --- Ajouter une colonne ---
@app.post("/add_column")
def add_column(title: str = Form(...), db: Session = Depends(get_db)):
    board = db.query(Board).first()
    if not board:
        raise HTTPException(status_code=404, detail="Tableau introuvable")
    column = Column(title=title, board_id=board.id)
    db.add(column)
    db.commit()
    db.refresh(column)
    return RedirectResponse("/board", status_code=302)

# --- Ajouter une carte ---
@app.post("/add_card/{column_id}")
def add_card(column_id: int, title: str = Form(...), db: Session = Depends(get_db)):
    card = Card(title=title, column_id=column_id)
    db.add(card)
    db.commit()
    db.refresh(card)
    return RedirectResponse("/board", status_code=302)
