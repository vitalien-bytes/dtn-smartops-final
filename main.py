import os
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, Board, Column, Card

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="DTN_SMARTOPS_SECRET_KEY")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "DTN-2025-secure-base")
BOARD_TITLE = os.getenv("BOARD_TITLE", "DTN SmartOps")

# --- Database Session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Page de login ---
@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        request.session["logged_in"] = True
        return RedirectResponse("/board", status_code=302)
    raise HTTPException(status_code=401, detail="Identifiants invalides")

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)

# --- Tableau principal ---
@app.get("/board", response_class=HTMLResponse)
def board(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logged_in"):
        return RedirectResponse("/", status_code=302)

    board = db.query(Board).first()
    if not board:
        board = Board(title=BOARD_TITLE)
        db.add(board)
        db.commit()
        db.refresh(board)

    columns = db.query(Column).filter(Column.board_id == board.id).all()
    return templates.TemplateResponse("board.html", {"request": request, "board": board, "columns": columns})

# --- Ajouter une colonne ---
@app.post("/add_column")
def add_column(title: str = Form(...), db: Session = Depends(get_db)):
    board = db.query(Board).first()
    column = Column(title=title, board_id=board.id)
    db.add(column)
    db.commit()
    return RedirectResponse("/board", status_code=302)

# --- Supprimer une colonne ---
@app.post("/delete_column/{col_id}")
def delete_column(col_id: int, db: Session = Depends(get_db)):
    db.query(Column).filter(Column.id == col_id).delete()
    db.commit()
    return RedirectResponse("/board", status_code=302)

# --- Ajouter une carte ---
@app.post("/add_card/{col_id}")
def add_card(col_id: int, description: str = Form(...), db: Session = Depends(get_db)):
    card = Card(description=description, column_id=col_id)
    db.add(card)
    db.commit()
    return RedirectResponse("/board", status_code=302)

# --- Supprimer une carte ---
@app.post("/delete_card/{card_id}")
def delete_card(card_id: int, db: Session = Depends(get_db)):
    db.query(Card).filter(Card.id == card_id).delete()
    db.commit()
    return RedirectResponse("/board", status_code=302)

# --- Déplacer une carte d'une colonne à une autre ---
@app.post("/move_card/{card_id}/{new_column_id}")
def move_card(card_id: int, new_column_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if card:
        card.column_id = new_column_id
        db.commit()
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Card not found")
