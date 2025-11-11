# DTN SmartOps (FastAPI)

## Déploiement Render
1) Crée un repo GitHub et uploade ces fichiers tel quel.
2) Sur Render: New → Web Service → connecte le repo.
3) Build: `pip install -r requirements.txt`  |  Start: `uvicorn main:app --host 0.0.0.0 --port 10000`
4) Settings → Environment (Add):
   - `DATABASE_URL` = URL Postgres Render (External Database URL)
   - `ADMIN_USER` = `admin`
   - `ADMIN_PASS` = `DTN-2025-secure-base`
   - `BOARD_TITLE` = `DTN SmartOps`
5) Deploy → ouvre l'URL. Login requis : admin / DTN-2025-secure-base
