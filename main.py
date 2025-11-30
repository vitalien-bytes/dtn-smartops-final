from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import os

app = FastAPI(title="DTN SmartOps API")

# On récupère l’URL de ta DB Render
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})

class Task(BaseModel):
    key: str
    title: str
    city: str
    category: str
    notes: str = ""

API_KEY = "FASTKEY"

@app.get("/tasks")
def get_tasks(key: str = Query(...)):
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Clé API invalide")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT title, city, category, notes FROM tasks"))
        tasks = [
            {"title": r.title, "city": r.city, "category": r.category, "notes": r.notes}
            for r in result
        ]
        return tasks

@app.post("/tasks")
def add_task(t: Task, key: str = Query(None)):
    if t.key != API_KEY:
        raise HTTPException(status_code=403, detail="Clé API invalide")

    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO tasks (title, city, category, notes) VALUES (:title, :city, :category, :notes)"),
            {"title": t.title, "city": t.city, "category": t.category, "notes": t.notes}
        )
    return {"success": True}
