import os, secrets
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from database import SessionLocal, engine
from models import Base, Board, Column, Card

# ---- App & sécurité session ----
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=secrets.token_hex(16))
app.mount("/static", StaticFiles(directory="static"), name="static")

Base.metadata.create_all(bind=engine)

# ---- Config login ----
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "DTN-2025-secure-base")
BOARD_TITLE = os.getenv("BOARD_TITLE", "DTN SmartOps")

# ---- jinja2 templates ----
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

# ---- DB dependency ----
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Auth ----------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if request.session.get("logged_in"):
        return RedirectResponse("/board", status_code=302)
    return RedirectResponse("/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "title": BOARD_TITLE})

@app.post("/login")
def do_login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        request.session["logged_in"] = True
        return RedirectResponse("/board", status_code=302)
    raise HTTPException(status_code=401, detail="Identifiants invalides")

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)

# ---------- Board ----------
@app.get("/board", response_class=HTMLResponse)
def show_board(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logged_in"):
        return RedirectResponse("/login", status_code=302)

    board = db.query(Board).first()
    if not board:
        board = Board(title=BOARD_TITLE)
        db.add(board)
        db.commit(); db.refresh(board)

        # colonnes exemple
        for name in ["devis acceptés", "Travaux programmés", "Factures à faire"]:
            db.add(Column(title=name, board_id=board.id))
        db.commit()

    columns = db.query(Column).filter(Column.board_id == board.id).all()
    cards_by_col = {c.id: db.query(Card).filter(Card.column_id == c.id).all() for c in columns}

    return templates.TemplateResponse(
        "board.html",
        {
            "request": request,
            "board": board,
            "columns": columns,
            "cards_by_col": cards_by_col,
        },
    )

# ---------- Colonnes : ajouter / renommer / supprimer ----------
@app.post("/add_column")
def add_column(name: str = Form(...), db: Session = Depends(get_db)):
    board = db.query(Board).first()
    if not board:
        raise HTTPException(status_code=400, detail="Board absent")
    db.add(Column(title=name.strip(), board_id=board.id))
    db.commit()
    return RedirectResponse("/board", status_code=302)

@app.post("/rename_column/{column_id}")
def rename_column(column_id: int, new_title: str = Form(...), db: Session = Depends(get_db)):
    col = db.query(Column).filter(Column.id == column_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Colonne introuvable")
    col.title = new_title.strip()
    db.commit()
    return RedirectResponse("/board", status_code=302)

@app.post("/delete_column/{column_id}")
def delete_column(column_id: int, db: Session = Depends(get_db)):
    col = db.query(Column).filter(Column.id == column_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Colonne introuvable")
    # supprimer les cartes associées
    db.query(Card).filter(Card.column_id == col.id).delete()
    db.delete(col)
    db.commit()
    return RedirectResponse("/board", status_code=302)

# ---------- Cartes : ajouter / supprimer / déplacer ----------
@app.post("/add_card/{column_id}")
def add_card(column_id: int, text: str = Form(...), db: Session = Depends(get_db)):
    text = text.strip()
    if not text:
        return RedirectResponse("/board", status_code=302)
    db.add(Card(title=text, column_id=column_id))
    db.commit()
    return RedirectResponse("/board", status_code=302)

@app.post("/delete_card/{card_id}")
def delete_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if card:
        db.delete(card)
        db.commit()
    return RedirectResponse("/board", status_code=302)

@app.post("/move_card/{card_id}/{new_column_id}")
def move_card(card_id: int, new_column_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Carte introuvable")
    card.column_id = new_column_id
    db.commit()
    return {"status": "ok"}
