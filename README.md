# Nova Hymnal Backend

A robust and scalable Django REST Framework backend for the Nova Hymnal Premium app.

## Features

- ✅ RESTful API with Django REST Framework
- ✅ Comprehensive models for Hymns, Categories, Authors, Verses, Sheet Music, and Audio
- ✅ Advanced filtering, searching, and pagination
- ✅ Admin interface for content management
- ✅ Media file handling (sheet music PDFs and audio files)
- ✅ Data seeding commands
- ✅ CORS configuration for mobile app
- ✅ Production-ready settings with environment variables
- ✅ Optional AWS S3 integration for media storage

## Project Structure

```
Nova-Hymnal-Backend/
├── config/                 # Django project configuration
│   ├── settings.py        # Settings with environment variables
│   ├── urls.py            # Root URL configuration
│   └── wsgi.py            # WSGI configuration
├── hymns/                 # Main app
│   ├── models.py          # Database models
│   ├── serializers.py    # DRF serializers
│   ├── views.py          # API viewsets
│   ├── urls.py           # App URLs
│   ├── admin.py          # Admin configuration
│   └── management/       # Management commands
│       └── commands/
│           ├── seed_data.py    # Seed hymns data
│           └── seed_media.py   # Seed media files
├── manage.py             # Django management script
├── requirements.txt      # Python dependencies
└── .env.example          # Environment variables template
```

## Installation

### 1. Prerequisites

- Python 3.8 or higher
- pip
- Virtual environment (recommended)

### 2. Setup

```bash
# Navigate to project directory
cd Nova-Hymnal-Backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env file with your settings
# (Update SECRET_KEY, database settings, etc.)

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Seed initial data
python manage.py seed_data
```

## API Endpoints

### Base URL: `/api/v1/`

### Categories
- `GET /api/v1/categories/` - List all categories
- `GET /api/v1/categories/{id}/` - Get category details

### Authors
- `GET /api/v1/authors/` - List all authors
- `GET /api/v1/authors/{id}/` - Get author details

### Hymns
- `GET /api/v1/hymns/` - List all hymns (with filtering, searching, pagination)
- `GET /api/v1/hymns/{id}/` - Get hymn details with verses
- `GET /api/v1/hymns/featured/` - Get featured hymns
- `GET /api/v1/hymns/daily/` - Get hymn of the day
- `GET /api/v1/hymns/{id}/sheet_music/` - Get sheet music for hymn
- `GET /api/v1/hymns/{id}/audio/{type}/` - Get audio file (piano, soprano, alto, tenor, bass)

**Query Parameters:**
- `category` - Filter by category ID
- `author` - Filter by author ID
- `language` - Filter by language
- `is_premium` - Filter by premium status
- `is_featured` - Filter featured hymns
- `search` - Search in title, number, author, category
- `ordering` - Order by number, title, created_at, view_count

### Sheet Music
- `GET /api/v1/sheet-music/` - List all sheet music
- `GET /api/v1/sheet-music/{id}/` - Get sheet music details

### Audio Files
- `GET /api/v1/audio/` - List all audio files
- `GET /api/v1/audio/{id}/` - Get audio file details

## Data Seeding

### Seed Hymn Data

```bash
# Seed with sample hymns
python manage.py seed_data

# Clear existing data and reseed
python manage.py seed_data --clear
```

### Seed Media Files

```bash
# Add sheet music
python manage.py seed_media \
    --hymn-id 101 \
    --type sheet_music \
    --file-path /path/to/sheet_music.pdf \
    --thumbnail-path /path/to/thumbnail.jpg

# Add audio file
python manage.py seed_media \
    --hymn-id 101 \
    --type audio \
    --audio-type piano \
    --file-path /path/to/piano.mp3
```

## Admin Interface

Access the admin interface at `/admin/` after creating a superuser:

```bash
python manage.py createsuperuser
```

The admin interface allows you to:
- Manage categories, authors, and hymns
- Upload sheet music and audio files
- Edit hymn content and metadata
- View statistics and analytics

## Development

### Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/v1/`

### Run Tests

```bash
python manage.py test
```

## Production Deployment

### Environment Variables

Update `.env` file with production settings:

```env
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,api.your-domain.com

# PostgreSQL Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=novahymnal
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=https://your-app-domain.com

# AWS S3 (Optional)
USE_S3=True
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
AWS_S3_REGION_NAME=us-east-1
```

### Database Migration

```bash
python manage.py migrate
python manage.py collectstatic
```

### Run with Gunicorn

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## Models

### Hymn
- Main hymn model with metadata
- Relationships: Category, Author
- Fields: number, title, language, scripture_references, history, etc.

### Verse
- Individual verses and choruses
- Relationship: Hymn (many-to-one)
- Fields: verse_number, is_chorus, text, order

### SheetMusic
- PDF sheet music files
- Relationship: Hymn (one-to-one)
- Fields: file, thumbnail, page_count, is_premium

### AudioFile
- Audio files (piano, vocal parts)
- Relationship: Hymn (many-to-one)
- Fields: audio_type, file, duration, bitrate, is_premium

### Category
- Hymn categories
- Fields: name, slug, description

### Author
- Hymn authors
- Fields: name, slug, biography, birth_year, death_year

## API Response Examples

### Get All Hymns
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/hymns/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "number": 101,
      "title": "Amazing Grace",
      "category": 1,
      "category_name": "Grace",
      "author": 1,
      "author_name": "John Newton",
      "language": "English",
      "is_premium": false
    }
  ]
}
```

### Get Hymn Details
```json
{
  "id": 1,
  "number": 101,
  "title": "Amazing Grace",
  "verses": [
    {
      "verse_number": 1,
      "is_chorus": false,
      "text": "Amazing grace! How sweet the sound..."
    }
  ],
  "sheet_music_url": "http://localhost:8000/media/sheet_music/...",
  "audio_urls": {
    "piano": "http://localhost:8000/media/audio/...",
    "soprano": "http://localhost:8000/media/audio/..."
  }
}
```

## License

Private - All rights reserved

