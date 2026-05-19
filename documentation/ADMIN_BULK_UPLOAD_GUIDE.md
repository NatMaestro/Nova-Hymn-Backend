# Admin Bulk Upload Guide

## Overview
The Nova Hymnal Backend admin interface includes bulk upload capabilities for efficient data management. All bulk upload options are accessible via buttons in the admin changelist pages.

## Accessing Bulk Upload

### 1. Hymns Bulk Upload
- Navigate to: **Admin → Hymns**
- Click the **"📤 Bulk Upload Hymns"** button at the top right
- Or go directly to: `/admin/hymns/hymn/bulk-upload/`

### 2. Sheet Music Bulk Upload
- Navigate to: **Admin → Sheet Music**
- Click the **"📤 Bulk Upload Sheet Music"** button at the top right
- Or go directly to: `/admin/hymns/sheetmusic/bulk-upload/`

### 3. Audio Files Bulk Upload
- Navigate to: **Admin → Audio Files**
- Click the **"📤 Bulk Upload Audio Files"** button at the top right
- Or go directly to: `/admin/hymns/audiofile/bulk-upload/`

## Bulk Upload Features

### 1. Hymns Bulk Upload

**Supported Formats:**
- Word Documents: `.docx`, `.doc`
- Text Files: `.txt`

**How It Works:**
1. Upload multiple Word or text files containing hymn lyrics
2. System automatically parses verses and choruses
3. Assign category and author (optional)
4. Set premium status for all hymns

**File Format Guidelines:**
```
101. Amazing Grace
1. Amazing grace! How sweet the sound...
2. 'Twas grace that taught my heart to fear...
Chorus: Amazing grace, how sweet the sound...
```

**Features:**
- Automatic verse extraction
- Chorus detection
- Auto-numbering if hymn number not found
- Batch category/author assignment

### 2. Sheet Music Bulk Upload

**Two Methods:**

#### Method 1: File Upload
- Upload multiple PDF files
- Filenames should contain hymn numbers (e.g., `101-sheet.pdf`, `hymn_102.pdf`)
- System automatically matches files to hymns

#### Method 2: URL Entry
- Enter hymn IDs and URLs in text format
- Format: `hymn_id|file_url|thumbnail_url|page_count`
- Example: `1|https://drive.google.com/file/...|https://thumbnail.url|2`

**Supported Sources:**
- Direct PDF file uploads
- External URLs (Google Drive, Dropbox, etc.)
- Both methods can be used together

### 3. Audio Files Bulk Upload

**Supported Formats:**
- MP3, WAV, M4A, AAC

**How It Works:**
1. Upload multiple audio files
2. Select audio type (piano, soprano, alto, tenor, bass, full)
3. System extracts hymn numbers from filenames
4. Automatically matches files to hymns

**Filename Examples:**
- `101-piano.mp3` → Hymn 101, Piano
- `hymn_102_soprano.wav` → Hymn 102, Soprano
- `103-alto.m4a` → Hymn 103, Alto

**Features:**
- Automatic hymn number detection
- Batch audio type assignment
- Premium status setting

## Tips for Bulk Upload

### Hymns
- Use consistent formatting in Word/text files
- Number verses clearly (1., 2., etc.)
- Mark choruses with "Chorus:" or "Refrain:"
- First line should contain hymn number and title

### Sheet Music
- For file uploads: Include hymn number in filename
- For URLs: Use the format shown in the interface
- Can mix file uploads and URLs in one batch
- Thumbnail URLs are optional

### Audio Files
- Include hymn number in filename
- Use consistent naming (e.g., `{number}-{type}.mp3`)
- All files in one batch will have the same audio type
- Upload different types separately

## Error Handling

The system provides detailed error messages:
- Missing hymn numbers → Error message with filename
- Duplicate entries → Warning message
- Invalid formats → Error with file/line details
- Summary shows: Created count and error count

## Best Practices

1. **Test with Small Batches First**: Upload 2-3 files to verify format
2. **Check Hymn Numbers**: Ensure hymns exist before uploading media
3. **Use Consistent Naming**: Makes bulk operations easier
4. **Review Error Messages**: Fix issues before large batches
5. **Backup Before Large Uploads**: Especially for production data

## Troubleshooting

### "Hymn number not found"
- Verify the hymn exists in the database
- Check the number format in filename
- Use the hymn ID reference table in the upload form

### "File format not supported"
- Check file extension matches supported formats
- Verify file is not corrupted
- Try a different file format

### "Already exists" warnings
- System skips duplicates to prevent data loss
- Update existing entries manually if needed
- Or delete existing entries before bulk upload

