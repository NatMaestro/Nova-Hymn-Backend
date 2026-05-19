# Backend preflight testing (before Render deploy)

Run these checks locally against your Neon database **before** deploying.

## Quick run

```bash
cd Nova-Hymnal-Backend
source venv/Scripts/activate   # Windows Git Bash
# or: .\venv\Scripts\activate    # PowerShell

python manage.py check
python manage.py migrate --check
python scripts/preflight_api_test.py
```

Exit code `0` = all tests passed.

## What the preflight script covers

| Area | Tests |
|------|--------|
| Django | `check`, migrations applied, WSGI import |
| Database | PostgreSQL engine + host |
| Public API | denominations, categories, authors, hymns (filtered + daily), sheet-music |
| Docs | `/swagger/`, admin login |
| Auth | register → login → profile → subscription status → verify (web platform) |
| Security | ALLOWED_HOSTS, SECRET_KEY (when `DEBUG=False`) |

## Manual smoke test (live server)

Terminal 1:

```bash
python manage.py runserver 0.0.0.0:8000
```

Terminal 2 (PowerShell):

```powershell
curl.exe http://localhost:8000/api/v1/denominations/
curl.exe "http://localhost:8000/api/v1/hymns/?denomination=1&hymn_period=new"
curl.exe http://localhost:8000/api/v1/hymns/daily/
```

Browse: http://localhost:8000/swagger/

## Production deploy checklist (Render)

0. **Python version** — Use **3.11** (not 3.14). Set in Render Dashboard → Environment → `PYTHON_VERSION` = `3.11.11`, or rely on `runtime.txt` in this folder. Root Directory must be `Nova-Hymnal-Backend` if deploying from the monorepo.

1. **Start command** (not `gunicorn app:app`):
   ```bash
   gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
   ```
2. **Build command**:
   ```bash
   pip install --upgrade pip setuptools wheel && pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
   ```
3. **Environment variables**:
   - `DEBUG=False`
   - `ENV=production`
   - `SECRET_KEY` — long random string (Render can generate)
   - `ALLOWED_HOSTS=nova-hymn-backend.onrender.com`
   - `DB_*` — Neon connection (host, user, password, name, port)
   - `DB_SSLMODE=require`
   - `CORS_ALLOW_ALL_ORIGINS=False`
   - `CORS_ALLOWED_ORIGINS=https://your-web-app.com,http://localhost:3000`
   - `CSRF_TRUSTED_ORIGINS=https://your-web-app.com`
4. After deploy, verify:
   ```bash
   curl https://nova-hymn-backend.onrender.com/api/v1/denominations/
   ```
   Response must be JSON with `"results"` (Django REST), not `"statusCode": 404`.

## Known issues fixed in preflight

- **Hymn detail 500**: Accessing `hymn.sheet_music` when none exists now handled safely in `HymnViewSet.retrieve`.
- **Render SSL**: `SECURE_PROXY_SSL_HEADER` set when `DEBUG=False`.
