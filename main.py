import os
import secrets
from typing import Generator

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select

from database import SessionLocal, engine
from models import Base, Board, Column, Card

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DTN SmartOps")
app.add_middleware(SessionMiddleware, secret_key=secrets.token_hex(16))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "DTN-2025-secure-base")
BOARD_TITLE = os.getenv("BOARD_TITLE", "DTN SmartOps")

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def do_login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        request.session["logged_in"] = True
        return RedirectResponse("/board", status_code=302)
    raise HTTPException(status_code=401, detail="Identifiants invalides")

@app.get("/board", response_class=HTMLResponse)
def board_view(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("logged_in"):
        return RedirectResponse("/", status_code=302)

    board = db.execute(select(Board).filter(Board.title == BOARD_TITLE)).scalar_one_or_none()
    if not board:
        board = Board(title=BOARD_TITLE)
        db.add(board); db.commit(); db.refresh(board)
        for name in ["À faire", "En cours", "Terminé"]:
            db.add(Column(title=name, board_id=board.id))
        db.commit()

    columns = db.execute(select(Column).filter(Column.board_id == board.id)).scalars().all()
    col_cards = {c.id: db.execute(select(Card).filter(Card.column_id == c.id).order_by(Card.position.asc())).scalars().all() for c in columns}
    return templates.TemplateResponse("board.html", {"request": request, "board": board, "columns": columns, "col_cards": col_cards})

@app.get("/health")
def health():
    return {"ok": True}
