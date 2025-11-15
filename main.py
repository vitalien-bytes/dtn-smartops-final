import os, secrets
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from database import SessionLocal, engine
from models import Base, Board, KanbanColumn, Card   # <-- IMPORTANT

# ---- App ----
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=secrets.token_hex(16))
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---- Création des tables ----
Base.metadata.create_all(bind=engine)

# ---- Login ----
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "DTN-2025-secure-base")
BOARD_TITLE = os.getenv("BOARD_TITLE", "DTN SmartOps")

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

# ---- DB ----
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---- Auth ----
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if request.session.get("logged_in"):
        return RedirectResponse("/board")
    return RedirectResponse("/login")

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
    return RedirectResponse("/login")

# ---- Board ----
@app.get("/board", response_class=HTMLResponse)
def show_board(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logged_in"):
        return RedirectResponse("/login")

    board = db.query(Board).first()
    if not board:
        board = Board(title=BOARD_TITLE)
        db.add(board)
        db.commit()
        db.refresh(board)

        # colonnes par défaut
        for name in ["devis acceptés", "Travaux programmés", "Factures à faire"]:
            db.add(KanbanColumn(title=name, board_id=board.id))
        db.commit()

    columns = db.query(KanbanColumn).filter(KanbanColumn.board_id == board.id).all()
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

# ---- Colonnes ----
@app.post("/add_column")
def add_column(name: str = Form(...), db: Session = Depends(get_db)):
    board = db.query(Board).first()
    if not board:
        raise HTTPException(status_code=400, detail="Board absent")
    db.add(KanbanColumn(title=name.strip(), board_id=board.id))
    db.commit()
    return RedirectResponse("/board", status_code=302)

@app.post("/rename_column/{column_id}")
def rename_column(column_id: int, new_title: str = Form(...), db: Session = Depends(get_db)):
    col = db.query(KanbanColumn).filter(KanbanColumn.id == column_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Colonne introuvable")
    col.title = new_title.strip()
    db.commit()
    return RedirectResponse("/board", status_code=302)

@app.post("/delete_column/{column_id}")
def delete_column(column_id: int, db: Session = Depends(get_db)):
    col = db.query(KanbanColumn).filter(KanbanColumn.id == column_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Colonne introuvable")
    db.query(Card).filter(Card.column_id == col.id).delete()
    db.delete(col)
    db.commit()
    return RedirectResponse("/board", status_code=302)

# ---- Cartes ----
@app.post("/add_card/{column_id}")
def add_card(column_id: int, text: str = Form(...), db: Session = Depends(get_db)):
    text = text.strip()
    if not text:
        return RedirectResponse("/board")
    db.add(Card(title=text, column_id=column_id))
    db.commit()
    return RedirectResponse("/board")

@app.post("/delete_card/{card_id}")
def delete_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if card:
        db.delete(card)
        db.commit()
    return RedirectResponse("/board")

@app.post("/move_card/{card_id}/{new_column_id}")
def move_card(card_id: int, new_column_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Carte introuvable")
    card.column_id = new_column_id
    db.commit()
    return {"status": "ok"}

# ---- Debug ----
from sqlalchemy import inspect
@app.get("/check-tables")
def check_tables(db=Depends(get_db)):
    inspector = inspect(db.bind)
    return {"tables": inspector.get_table_names()}

@app.get("/debug-rows")
def debug_rows(db: Session = Depends(get_db)):
    boards = db.query(Board).all()
    cols = db.query(KanbanColumn).all() if 'KanbanColumn' in globals() else db.query(Column).all()
    cards = db.query(Card).all()

    return {
        "boards_count": len(boards),
        "columns_count": len(cols),
        "cards_count": len(cards),
        "boards": [b.title for b in boards],
        "columns": [c.title for c in cols],
        "cards": [c.title for c in cards],
    }
