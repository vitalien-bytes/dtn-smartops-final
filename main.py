import os, secrets
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import inspect

from database import SessionLocal, engine
from models import Base, Board, KanbanColumn, Card

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=secrets.token_hex(16))
app.mount("/static", StaticFiles(directory="static"), name="static")

Base.metadata.create_all(bind=engine)

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "DTN-2025-secure-base")
BOARD_TITLE = os.getenv("BOARD_TITLE", "DTN SmartOps")

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------- Auth --------------------

@app.get("/")
def home(request: Request):
    if request.session.get("logged_in"):
        return RedirectResponse("/board", status_code=302)
    return RedirectResponse("/login")

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "title": BOARD_TITLE})

@app.post("/login")
def do_login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        request.session["logged_in"] = True
        return RedirectResponse("/board", status_code=302)
    raise HTTPException(401, "Identifiants invalides")

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)

# -------------------- Board --------------------

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

        for name in ["devis acceptés", "Travaux programmés", "Factures à faire"]:
            db.add(KanbanColumn(title=name, board_id=board.id))
        db.commit()

    columns = db.query(KanbanColumn).filter(KanbanColumn.board_id == board.id).all()
    cards_by_col = {c.id: db.query(Card).filter(Card.column_id == c.id).all() for c in columns}

    return templates.TemplateResponse(
        "board.html",
        {"request": request, "board": board, "columns": columns, "cards_by_col": cards_by_col},
    )

# -------------------- Columns --------------------

@app.post("/add_column")
def add_column(name: str = Form(...), db: Session = Depends(get_db)):
    board = db.query(Board).first()
    if not board:
        raise HTTPException(400, "Board manquant")
    db.add(KanbanColumn(title=name.strip(), board_id=board.id))
    db.commit()
    return RedirectResponse("/board", status_code=302)

@app.post("/rename_column/{column_id}")
def rename_column(column_id: int, new_title: str = Form(...), db: Session = Depends(get_db)):
    col = db.query(KanbanColumn).filter(KanbanColumn.id == column_id).first()
    if not col:
        raise HTTPException(404, "Colonne introuvable")
    col.title = new_title.strip()
    db.commit()
    return RedirectResponse("/board", status_code=302)

@app.post("/delete_column/{column_id}")
def delete_column(column_id: int, db: Session = Depends(get_db)):
    col = db.query(KanbanColumn).filter(KanbanColumn.id == column_id).first()
    if col:
        db.query(Card).filter(Card.column_id == col.id).delete()
        db.delete(col)
        db.commit()
    return RedirectResponse("/board", status_code=302)

# -------------------- Cards --------------------

@app.post("/add_card/{column_id}")
def add_card(column_id: int, text: str = Form(...), db: Session = Depends(get_db)):
    if not text.strip():
        return RedirectResponse("/board", status_code=302)

    col = db.query(KanbanColumn).filter(KanbanColumn.id == column_id).first()
    if not col:
        raise HTTPException(404, "Colonne introuvable")

    new_card = Card(title=text.strip(), column_id=column_id)
    db.add(new_card)
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
        raise HTTPException(404, "Carte introuvable")
    card.column_id = new_column_id
    db.commit()
    return {"status": "ok"}

# -------------------- DEBUG --------------------

@app.get("/debug-rows")
def debug_rows(db=Depends(get_db)):
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    data = {}

    for t in tables:
        rows = list(db.execute(f"SELECT * FROM {t};"))
        data[t] = [dict(r) for r in rows]

    return {
        "boards_count": len(data.get("boards", [])),
        "columns_count": len(data.get("columns", [])),
        "cards_count": len(data.get("cards", [])),
        "boards": [row.get("title") for row in data.get("boards", [])],
        "columns": [row.get("title") for row in data.get("columns", [])],
        "cards": [row.get("title") for row in data.get("cards", [])],
    }
