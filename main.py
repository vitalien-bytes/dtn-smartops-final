import os
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from database import SessionLocal, engine
from models import Base, Board, Column, Card

Base.metadata.create_all(bind=engine)

app = FastAPI()  # ✅ C’est cette ligne que Render cherche
app.add_middleware(SessionMiddleware, secret_key=os.urandom(16))
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "DTN-2025-secure-base")
BOARD_TITLE = os.getenv("BOARD_TITLE", "DTN SmartOps")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        request.session["logged_in"] = True
        return RedirectResponse("/board", status_code=302)
    raise HTTPException(status_code=401, detail="Identifiants invalides")


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
    return templates.TemplateResponse(
        "board.html",
        {"request": request, "board": board, "columns": columns},
    )
