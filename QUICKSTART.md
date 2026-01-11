# Quick Start Guide

## Initial Setup (First Time)

### 1. Install Dependencies

```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
copy env.example .env  # Windows
# or
cp env.example .env   # macOS/Linux

# Edit .env file and set:
# - SECRET_KEY (generate a new one)
# - DEBUG=True for development
# - Database settings (SQLite for development is fine)
```

### 3. Initialize Database

```bash
# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser
# Follow prompts to create username, email, and password
```

### 4. Seed Initial Data

```bash
# Seed sample hymns, categories, and authors
python manage.py seed_data
```

### 5. Start Development Server

```bash
python manage.py runserver
```

The API will be available at: `http://localhost:8000/api/v1/`
Admin panel: `http://localhost:8000/admin/`

## Adding Media Files

### Add Sheet Music

```bash
python manage.py seed_media \
    --hymn-id 101 \
    --type sheet_music \
    --file-path "C:\path\to\sheet_music.pdf" \
    --thumbnail-path "C:\path\to\thumbnail.jpg"
```

### Add Audio Files

```bash
# Piano accompaniment
python manage.py seed_media \
    --hymn-id 101 \
    --type audio \
    --audio-type piano \
    --file-path "C:\path\to\piano.mp3"

# Vocal parts
python manage.py seed_media \
    --hymn-id 101 \
    --type audio \
    --audio-type soprano \
    --file-path "C:\path\to\soprano.mp3"
```

## Testing the API

### Using curl

```bash
# Get all hymns
curl http://localhost:8000/api/v1/hymns/

# Get hymn by ID
curl http://localhost:8000/api/v1/hymns/1/

# Get categories
curl http://localhost:8000/api/v1/categories/

# Get hymn of the day
curl http://localhost:8000/api/v1/hymns/daily/

# Search hymns
curl "http://localhost:8000/api/v1/hymns/?search=amazing"
```

### Using Browser

Visit these URLs in your browser:
- `http://localhost:8000/api/v1/hymns/`
- `http://localhost:8000/api/v1/categories/`
- `http://localhost:8000/api/v1/hymns/daily/`

## Common Commands

```bash
# Create new migration after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Access Django shell
python manage.py shell

# Collect static files (for production)
python manage.py collectstatic

# Clear database and reseed
python manage.py seed_data --clear
```

## Troubleshooting

### Port Already in Use

```bash
# Use a different port
python manage.py runserver 8001
```

### Migration Issues

```bash
# Reset database (SQLite only - deletes all data!)
# Delete db.sqlite3 file, then:
python manage.py migrate
python manage.py seed_data
```

### Import Errors

```bash
# Make sure virtual environment is activated
# Reinstall dependencies
pip install -r requirements.txt
```

## Next Steps

1. Update the frontend API URL in `Nova-Hymnal-Premium/lib/api.ts` to point to your backend
2. Test API endpoints with your mobile app
3. Add more hymns using the admin interface or seed commands
4. Configure production settings when ready to deploy

