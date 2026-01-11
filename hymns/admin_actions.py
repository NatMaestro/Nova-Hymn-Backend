"""
Admin actions for bulk uploads and data management
"""
import re
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from docx import Document
from .models import Hymn, Verse, Category, Author, SheetMusic, AudioFile


def parse_word_document(file):
    """Parse Word document and extract hymn data"""
    try:
        doc = Document(file)
        hymn_data = {
            'title': '',
            'number': None,
            'verses': [],
            'author': '',
            'category': '',
            'language': 'English',
        }
        
        current_verse = None
        verse_number = 1
        title_found = False
        number_found = False
        
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue
            
            # Try to extract hymn number from patterns like:
            # "NCH 1", "OCH 2", "101. Title", "1. Title", or just "101"
            if not number_found:
                # Pattern 1: "NCH 1", "OCH 2", etc. (prefix + number)
                prefix_match = re.match(r'^[A-Z]+\s+(\d+)$', text)
                if prefix_match:
                    hymn_data['number'] = int(prefix_match.group(1))
                    number_found = True
                    continue
                
                # Pattern 2: "101. Amazing Grace" or "1. Amazing Grace"
                title_match = re.match(r'^(\d+)\.\s*(.+)$', text)
                if title_match:
                    hymn_data['number'] = int(title_match.group(1))
                    hymn_data['title'] = title_match.group(2)
                    title_found = True
                    number_found = True
                    continue
                
                # Pattern 3: Just a number "101" or "1"
                number_only_match = re.match(r'^(\d+)$', text)
                if number_only_match:
                    hymn_data['number'] = int(number_only_match.group(1))
                    number_found = True
                    continue
            
            # Try to extract title from first non-number paragraph
            if not title_found and number_found:
                # If we have a number but no title, use first non-verse line as title
                # But skip if it looks like a verse (starts with number)
                if not re.match(r'^(\d+)\.', text):
                    hymn_data['title'] = text
                    title_found = True
                    continue
            
            # If we still don't have a title and this is the first content, use it as title
            if not title_found:
                # Check if it's a verse number - if so, extract title from first verse
                verse_match = re.match(r'^(\d+)\.', text)
                if verse_match:
                    # Use first few words of first verse as title if no title found
                    verse_text = re.sub(r'^\d+\.\s*', '', text)
                    # Take first 50 characters as title
                    hymn_data['title'] = verse_text[:50].strip()
                    if len(verse_text) > 50:
                        hymn_data['title'] += '...'
                    title_found = True
                    # Continue to process this as a verse below
                else:
                    hymn_data['title'] = text
                    title_found = True
                    continue
            
            # Check if it's a verse number or chorus
            verse_match = re.match(r'^(\d+)\.', text)
            chorus_match = re.match(r'^(Chorus|Refrain):?', text, re.IGNORECASE)
            
            if verse_match:
                # Save previous verse if exists
                if current_verse:
                    hymn_data['verses'].append(current_verse)
                
                verse_number = int(verse_match.group(1))
                verse_text = re.sub(r'^\d+\.\s*', '', text)
                current_verse = {
                    'verse_number': verse_number,
                    'is_chorus': False,
                    'text': verse_text,
                    'order': verse_number
                }
            elif chorus_match:
                # Save previous verse if exists
                if current_verse:
                    hymn_data['verses'].append(current_verse)
                
                verse_text = re.sub(r'^(Chorus|Refrain):?\s*', '', text, flags=re.IGNORECASE)
                current_verse = {
                    'verse_number': verse_number,
                    'is_chorus': True,
                    'text': verse_text,
                    'order': verse_number + 100  # Put chorus after verses
                }
            elif current_verse:
                # Continue current verse
                current_verse['text'] += '\n' + text
            else:
                # New verse without number
                current_verse = {
                    'verse_number': verse_number,
                    'is_chorus': False,
                    'text': text,
                    'order': verse_number
                }
                verse_number += 1
        
        # Add last verse
        if current_verse:
            hymn_data['verses'].append(current_verse)
        
        return hymn_data
    except Exception as e:
        raise Exception(f"Error parsing Word document: {str(e)}")


def parse_text_file(file):
    """Parse plain text file and extract hymn data"""
    try:
        content = file.read().decode('utf-8')
        lines = content.split('\n')
        
        hymn_data = {
            'title': '',
            'number': None,
            'verses': [],
            'author': '',
            'category': '',
            'language': 'English',
        }
        
        current_verse = None
        verse_number = 1
        title_found = False
        number_found = False
        
        for line in lines:
            text = line.strip()
            if not text:
                continue
            
            # Try to extract hymn number from patterns like:
            # "NCH 1", "OCH 2", "101. Title", "1. Title", or just "101"
            if not number_found:
                # Pattern 1: "NCH 1", "OCH 2", etc. (prefix + number)
                prefix_match = re.match(r'^[A-Z]+\s+(\d+)$', text)
                if prefix_match:
                    hymn_data['number'] = int(prefix_match.group(1))
                    number_found = True
                    continue
                
                # Pattern 2: "101. Amazing Grace" or "1. Amazing Grace"
                title_match = re.match(r'^(\d+)\.\s*(.+)$', text)
                if title_match:
                    hymn_data['number'] = int(title_match.group(1))
                    hymn_data['title'] = title_match.group(2)
                    title_found = True
                    number_found = True
                    continue
                
                # Pattern 3: Just a number "101" or "1"
                number_only_match = re.match(r'^(\d+)$', text)
                if number_only_match:
                    hymn_data['number'] = int(number_only_match.group(1))
                    number_found = True
                    continue
            
            # Try to extract title from first non-number line
            if not title_found and number_found:
                # If we have a number but no title, use first non-verse line as title
                # But skip if it looks like a verse (starts with number)
                if not re.match(r'^(\d+)\.', text):
                    hymn_data['title'] = text
                    title_found = True
                    continue
            
            # If we still don't have a title and this is the first content, use it as title
            if not title_found:
                # Check if it's a verse number - if so, extract title from first verse
                verse_match = re.match(r'^(\d+)\.', text)
                if verse_match:
                    # Use first few words of first verse as title if no title found
                    verse_text = re.sub(r'^\d+\.\s*', '', text)
                    # Take first 50 characters as title
                    hymn_data['title'] = verse_text[:50].strip()
                    if len(verse_text) > 50:
                        hymn_data['title'] += '...'
                    title_found = True
                    # Continue to process this as a verse below
                else:
                    hymn_data['title'] = text
                    title_found = True
                    continue
            
            # Check if it's a verse number or chorus
            verse_match = re.match(r'^(\d+)\.', text)
            chorus_match = re.match(r'^(Chorus|Refrain):?', text, re.IGNORECASE)
            
            if verse_match:
                if current_verse:
                    hymn_data['verses'].append(current_verse)
                
                verse_number = int(verse_match.group(1))
                verse_text = re.sub(r'^\d+\.\s*', '', text)
                current_verse = {
                    'verse_number': verse_number,
                    'is_chorus': False,
                    'text': verse_text,
                    'order': verse_number
                }
            elif chorus_match:
                if current_verse:
                    hymn_data['verses'].append(current_verse)
                
                verse_text = re.sub(r'^(Chorus|Refrain):?\s*', '', text, flags=re.IGNORECASE)
                current_verse = {
                    'verse_number': verse_number,
                    'is_chorus': True,
                    'text': verse_text,
                    'order': verse_number + 100
                }
            elif current_verse:
                current_verse['text'] += '\n' + text
            else:
                current_verse = {
                    'verse_number': verse_number,
                    'is_chorus': False,
                    'text': text,
                    'order': verse_number
                }
                verse_number += 1
        
        if current_verse:
            hymn_data['verses'].append(current_verse)
        
        return hymn_data
    except Exception as e:
        raise Exception(f"Error parsing text file: {str(e)}")


@admin.action(description='Bulk upload hymns from Word/Text files')
def bulk_upload_hymns(modeladmin, request, queryset):
    """Admin action for bulk uploading hymns"""
    if request.method == 'POST':
        files = request.FILES.getlist('files')
        category_id = request.POST.get('category')
        author_id = request.POST.get('author')
        is_premium = request.POST.get('is_premium') == 'on'
        
        if not files:
            messages.error(request, 'Please select at least one file')
            return redirect(request.path)
        
        category = Category.objects.get(id=category_id) if category_id else None
        author = Author.objects.get(id=author_id) if author_id else None
        
        created_count = 0
        error_count = 0
        
        with transaction.atomic():
            for file in files:
                try:
                    file_extension = file.name.split('.')[-1].lower()
                    
                    if file_extension in ['docx', 'doc']:
                        hymn_data = parse_word_document(file)
                    elif file_extension in ['txt', 'text']:
                        hymn_data = parse_text_file(file)
                    else:
                        messages.error(request, f'Unsupported file format: {file_extension}')
                        error_count += 1
                        continue
                    
                    # Get or create hymn
                    hymn_number = hymn_data.get('number')
                    if not hymn_number:
                        # Auto-assign number if not provided
                        last_hymn = Hymn.objects.order_by('-number').first()
                        hymn_number = (last_hymn.number + 1) if last_hymn else 1
                    
                    hymn, created = Hymn.objects.get_or_create(
                        number=hymn_number,
                        defaults={
                            'title': hymn_data.get('title', 'Untitled Hymn'),
                            'category': category or hymn_data.get('category'),
                            'author': author or hymn_data.get('author'),
                            'language': hymn_data.get('language', 'English'),
                            'is_premium': is_premium,
                        }
                    )
                    
                    if created:
                        # Add verses
                        for verse_data in hymn_data.get('verses', []):
                            Verse.objects.create(
                                hymn=hymn,
                                verse_number=verse_data['verse_number'],
                                is_chorus=verse_data.get('is_chorus', False),
                                text=verse_data['text'],
                                order=verse_data.get('order', verse_data['verse_number'])
                            )
                        created_count += 1
                    else:
                        messages.warning(request, f'Hymn {hymn_number} already exists, skipped')
                
                except Exception as e:
                    messages.error(request, f'Error processing {file.name}: {str(e)}')
                    error_count += 1
        
        messages.success(request, f'Successfully created {created_count} hymns. {error_count} errors.')
        return redirect('admin:hymns_hymn_changelist')
    
    # Render upload form
    categories = Category.objects.all()
    authors = Author.objects.all()
    return render(request, 'admin/bulk_upload_hymns.html', {
        'categories': categories,
        'authors': authors,
    })

