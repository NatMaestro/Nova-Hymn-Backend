# Nova Hymnal Backend - Complete Feature Documentation

## Overview
This backend provides a comprehensive REST API for the Nova Hymnal Premium mobile app, supporting both free and premium features with secure subscription management.

## Features Implemented

### 1. User Authentication & Management
- **Custom User Model**: Extended Django's AbstractUser with premium status tracking
- **JWT Authentication**: Secure token-based authentication
- **User Registration**: `/api/v1/auth/register/`
- **User Login**: `/api/v1/auth/login/`
- **User Profile**: `/api/v1/auth/profile/`
- **Token Refresh**: `/api/v1/auth/refresh/`

### 2. Subscription Management
- **Subscription Model**: Tracks in-app purchases from iOS/Android
- **Subscription Verification**: `/api/v1/subscriptions/verify/`
- **Subscription Status**: `/api/v1/subscriptions/status/`
- **Subscription CRUD**: Full REST API for subscription management
- **Automatic Premium Status**: Updates user premium status automatically

### 3. Favorites System
- **Favorites Model**: User-specific hymn favorites
- **Free User Limit**: 10 favorites maximum
- **Premium Unlimited**: No limit for premium users
- **Endpoints**:
  - `GET /api/v1/favorites/` - List user favorites
  - `POST /api/v1/favorites/` - Add favorite
  - `DELETE /api/v1/favorites/{id}/` - Remove favorite
  - `DELETE /api/v1/favorites/remove/` - Remove by hymn ID

### 4. Playlists
- **Playlist Model**: User-created playlists
- **Playlist Management**: Full CRUD operations
- **Hymn Ordering**: Maintains order of hymns in playlists
- **Public/Private**: Playlists can be shared publicly
- **Endpoints**:
  - `GET /api/v1/playlists/` - List playlists
  - `POST /api/v1/playlists/` - Create playlist
  - `GET /api/v1/playlists/{id}/` - Get playlist details
  - `POST /api/v1/playlists/{id}/add_hymn/` - Add hymn to playlist
  - `DELETE /api/v1/playlists/{id}/remove_hymn/` - Remove hymn from playlist

### 5. Hymn Notes/Annotations
- **HymnNote Model**: User notes for hymns
- **Public/Private Notes**: Users can share notes publicly
- **Endpoints**:
  - `GET /api/v1/notes/` - List notes (own + public)
  - `POST /api/v1/notes/` - Create note
  - `GET /api/v1/notes/{id}/` - Get note
  - `PUT/PATCH /api/v1/notes/{id}/` - Update note
  - `DELETE /api/v1/notes/{id}/` - Delete note

### 6. Premium Content Protection
- **Sheet Music Protection**: Premium sheet music only accessible to premium users
- **Audio Protection**: Premium audio files protected
- **Automatic Filtering**: Free users see filtered content automatically
- **Secure Endpoints**: All premium endpoints check subscription status

### 7. Enhanced Sheet Music Support
- **File Upload**: Direct PDF file uploads
- **URL Support**: External URLs (Google Drive, Dropbox, etc.)
- **Thumbnail Support**: Both file and URL thumbnails
- **Flexible Storage**: Choose file upload OR URL

### 8. Admin Interface Enhancements
- **Bulk Upload**: Upload multiple hymns from Word/Text files
- **File Parsing**: Automatic parsing of .docx, .doc, .txt files
- **Verse Extraction**: Automatically extracts verses and choruses
- **Category/Author Assignment**: Bulk assign during upload
- **Comprehensive Admin**: Full admin interface for all models

### 9. Security Features
- **JWT Authentication**: Secure token-based auth
- **Premium Content Gates**: All premium content protected
- **User Isolation**: Users can only access their own data
- **Rate Limiting**: Configurable rate limiting (via django-ratelimit)
- **Input Validation**: Comprehensive validation on all endpoints

## API Endpoints

### Authentication
```
POST /api/v1/auth/register/          # Register new user
POST /api/v1/auth/login/             # Login (get JWT tokens)
POST /api/v1/auth/refresh/           # Refresh JWT token
GET  /api/v1/auth/profile/            # Get current user profile
```

### Hymns
```
GET  /api/v1/hymns/                  # List all hymns (paginated)
GET  /api/v1/hymns/{id}/             # Get hymn details
GET  /api/v1/hymns/featured/         # Get featured hymns
GET  /api/v1/hymns/daily/            # Get hymn of the day
GET  /api/v1/hymns/{id}/sheet_music/ # Get sheet music (premium)
GET  /api/v1/hymns/{id}/audio/{type}/ # Get audio file (premium)
```

### Subscriptions
```
GET    /api/v1/subscriptions/        # List user subscriptions
POST   /api/v1/subscriptions/        # Create subscription
POST   /api/v1/subscriptions/verify/ # Verify app store purchase
GET    /api/v1/subscriptions/status/ # Get subscription status
GET    /api/v1/subscriptions/{id}/   # Get subscription details
PUT    /api/v1/subscriptions/{id}/   # Update subscription
DELETE /api/v1/subscriptions/{id}/   # Cancel subscription
```

### Favorites
```
GET    /api/v1/favorites/            # List user favorites
POST   /api/v1/favorites/            # Add favorite
DELETE /api/v1/favorites/{id}/       # Remove favorite
DELETE /api/v1/favorites/remove/     # Remove by hymn ID
```

### Playlists
```
GET    /api/v1/playlists/            # List playlists
POST   /api/v1/playlists/            # Create playlist
GET    /api/v1/playlists/{id}/       # Get playlist
PUT    /api/v1/playlists/{id}/       # Update playlist
DELETE /api/v1/playlists/{id}/      # Delete playlist
POST   /api/v1/playlists/{id}/add_hymn/    # Add hymn
DELETE /api/v1/playlists/{id}/remove_hymn/ # Remove hymn
```

### Notes
```
GET    /api/v1/notes/                # List notes
POST   /api/v1/notes/                # Create note
GET    /api/v1/notes/{id}/           # Get note
PUT    /api/v1/notes/{id}/           # Update note
DELETE /api/v1/notes/{id}/          # Delete note
```

## Admin Interface Features

### Bulk Upload Hymns
1. Navigate to Hymns admin page
2. Click "Bulk Upload Hymns" action or go to `/admin/hymns/hymn/bulk-upload/`
3. Select multiple files (.docx, .doc, .txt)
4. Choose category and author (optional)
5. Set premium status
6. Upload - system automatically parses and creates hymns

### File Format Support
- **Word Documents** (.docx, .doc): Full parsing with verse extraction
- **Text Files** (.txt): Plain text parsing
- **Audio Files**: MP3, WAV, M4A (via AudioFile model)
- **Sheet Music**: PDF files or external URLs

## Security Considerations

1. **JWT Tokens**: Secure token-based authentication
2. **Premium Gates**: All premium content requires active subscription
3. **User Isolation**: Users can only access their own data
4. **Input Validation**: All inputs validated and sanitized
5. **Rate Limiting**: Configurable rate limits on endpoints
6. **CORS**: Properly configured for mobile app origins
7. **File Upload Limits**: 10MB max file size

## Database Models

### Core Models
- `User` - Custom user with premium tracking
- `Category` - Hymn categories
- `Author` - Hymn authors
- `Hymn` - Main hymn model
- `Verse` - Hymn verses/choruses

### Media Models
- `SheetMusic` - PDF files or URLs
- `AudioFile` - Audio files (piano, vocal parts)

### User-Specific Models
- `Subscription` - Premium subscriptions
- `Favorite` - User favorites
- `Playlist` - User playlists
- `PlaylistHymn` - Playlist-hymn relationship
- `HymnNote` - User notes/annotations

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   - Copy `env.example` to `.env`
   - Set `SECRET_KEY`, database settings, etc.

3. **Run Migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

5. **Run Server**:
   ```bash
   python manage.py runserver
   ```

## Next Steps

1. **Create Admin Template**: Add `templates/admin/bulk_upload_hymns.html` for bulk upload UI
2. **Add Rate Limiting**: Configure django-ratelimit for production
3. **Set Up Celery**: For async tasks (optional)
4. **Configure S3**: For production file storage (optional)
5. **Add Analytics**: Track usage and popular hymns
6. **Implement Caching**: Redis caching for better performance

## Notes

- All premium features are automatically protected
- Free users have a 10-favorite limit enforced
- Sheet music supports both file uploads and external URLs
- Bulk upload automatically parses verses from Word/text files
- Subscription status is automatically synced with user premium status

