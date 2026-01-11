# Complete Setup Instructions

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (optional)

## Step-by-Step Setup

### Step 1: Navigate to Backend Directory

```bash
cd Nova-Hymnal-Backend
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```bash
# Copy the example file
copy env.example .env  # Windows
# or
cp env.example .env   # macOS/Linux
```

Edit `.env` file:

```env
SECRET_KEY=django-insecure-your-secret-key-here-change-this
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# CORS (for mobile app)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:19006
```

**Important:** Generate a secure SECRET_KEY:
```python
# Run in Python shell
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### Step 5: Run Database Migrations

```bash
python manage.py migrate
```

This creates the database tables.

### Step 6: Create Admin User

```bash
python manage.py createsuperuser
```

Enter:
- Username
- Email (optional)
- Password (twice)

### Step 7: Seed Initial Data

```bash
python manage.py seed_data
```

This creates:
- 5 sample categories
- 5 sample authors
- 5 sample hymns with verses

### Step 8: Start Development Server

```bash
python manage.py runserver
```

Server runs at: `http://localhost:8000`

## Verify Installation

1. **Check API**: Visit `http://localhost:8000/api/v1/hymns/`
2. **Check Admin**: Visit `http://localhost:8000/admin/` and login
3. **Check Categories**: Visit `http://localhost:8000/api/v1/categories/`

## Adding Your Own Data

### Option 1: Using Admin Interface

1. Go to `http://localhost:8000/admin/`
2. Login with superuser credentials
3. Add Categories, Authors, Hymns, etc.
4. Upload sheet music and audio files

### Option 2: Using Management Commands

```bash
# Seed more data
python manage.py seed_data

# Add sheet music
python manage.py seed_media --hymn-id 101 --type sheet_music --file-path "path/to/file.pdf"

# Add audio
python manage.py seed_media --hymn-id 101 --type audio --audio-type piano --file-path "path/to/audio.mp3"
```

## Connecting Frontend to Backend

Update `Nova-Hymnal-Premium/lib/api.ts`:

```typescript
const api = axios.create({
  baseURL: "http://localhost:8000/api/v1",  // Development
  // baseURL: "https://your-production-api.com/api/v1",  // Production
  headers: {
    "Content-Type": "application/json",
  },
});
```

## Production Deployment

### 1. Update Settings

Edit `.env`:
```env
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,api.your-domain.com

# PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=novahymnal
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=your_host
DB_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=https://your-app-domain.com
```

### 2. Collect Static Files

```bash
python manage.py collectstatic
```

### 3. Run with Gunicorn

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/hymns/` | GET | List all hymns |
| `/api/v1/hymns/{id}/` | GET | Get hymn details |
| `/api/v1/hymns/featured/` | GET | Get featured hymns |
| `/api/v1/hymns/daily/` | GET | Get hymn of the day |
| `/api/v1/hymns/{id}/sheet_music/` | GET | Get sheet music |
| `/api/v1/hymns/{id}/audio/{type}/` | GET | Get audio file |
| `/api/v1/categories/` | GET | List categories |
| `/api/v1/authors/` | GET | List authors |
| `/api/v1/sheet-music/` | GET | List all sheet music |
| `/api/v1/audio/` | GET | List all audio files |

## Support

For issues or questions, check:
- `README.md` - Full documentation
- `QUICKSTART.md` - Quick reference
- Django documentation: https://docs.djangoproject.com/
- DRF documentation: https://www.django-rest-framework.org/

