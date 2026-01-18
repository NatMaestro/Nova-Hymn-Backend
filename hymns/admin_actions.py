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
    """Parse Word document and extract hymn data - supports multiple hymns in one document"""
    try:
        doc = Document(file)
        all_hymns = []
        
        current_hymn = None
        current_verse = None
        verse_number = 1
        title_found = False
        number_found = False
        blank_lines_count = 0
        
        def save_current_hymn():
            """Save the current hymn if it has data"""
            nonlocal current_hymn, current_verse, verse_number, title_found, number_found
            if current_hymn and (current_hymn.get('number') is not None or current_hymn.get('verses')):
                # Add last verse
                if current_verse:
                    current_hymn['verses'].append(current_verse)
                    current_verse = None
                # Only add if it has verses or a valid number
                if current_hymn.get('verses') or current_hymn.get('number'):
                    all_hymns.append(current_hymn)
            # Reset for next hymn
            current_hymn = {
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
        
        def is_new_hymn_start(text):
            """Check if this line indicates a new hymn"""
            # Skip header lines (like "THE NEW CATHOLIC HYMNAL, 2021")
            if re.match(r'^THE\s+NEW\s+CATHOLIC\s+HYMNAL', text, re.IGNORECASE):
                return False, None
            
            # Pattern 1: "NCH 1", "OCH 2", etc. (prefix + number)
            prefix_match = re.match(r'^[A-Z]{2,}\s+(\d+)$', text)
            if prefix_match:
                return True, int(prefix_match.group(1))
            
            # Pattern 2: "101. Amazing Grace" or "1. Amazing Grace"
            title_match = re.match(r'^(\d+)\.\s*(.+)$', text)
            if title_match:
                return True, (int(title_match.group(1)), title_match.group(2))
            
            # Pattern 3: Just a number "101" or "1" (but only if we're starting fresh or after a hymn with verses)
            number_only_match = re.match(r'^(\d+)$', text)
            if number_only_match:
                # Only treat as new hymn if:
                # 1. We don't have a current hymn yet, OR
                # 2. Current hymn has verses (meaning we've finished it), OR
                # 3. Current hymn has a number and this is a different number
                if not current_hymn:
                    return True, int(number_only_match.group(1))
                elif current_hymn.get('verses'):
                    return True, int(number_only_match.group(1))
                elif current_hymn.get('number') and int(number_only_match.group(1)) != current_hymn.get('number'):
                    return True, int(number_only_match.group(1))
            
            return False, None
        
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            
            # Track blank lines
            if not text:
                blank_lines_count += 1
                # Multiple blank lines might indicate hymn separation
                if blank_lines_count >= 2 and current_hymn and current_hymn.get('verses'):
                    # Save current hymn if it has verses
                    save_current_hymn()
                    blank_lines_count = 0
                continue
            else:
                blank_lines_count = 0
            
            # Skip header lines
            if re.match(r'^THE\s+NEW\s+CATHOLIC\s+HYMNAL', text, re.IGNORECASE):
                continue
            
            # Check if this is a new hymn start
            is_new, hymn_info = is_new_hymn_start(text)
            if is_new:
                # Save previous hymn if exists and has verses
                if current_hymn and current_hymn.get('verses'):
                    save_current_hymn()
                
                # Start new hymn
                if isinstance(hymn_info, tuple):
                    # Pattern 2: number and title together
                    current_hymn = {
                        'title': hymn_info[1],
                        'number': hymn_info[0],
                        'verses': [],
                        'author': '',
                        'category': '',
                        'language': 'English',
                    }
                    number_found = True
                    title_found = True
                else:
                    # Pattern 1 or 3: just number
                    current_hymn = {
                        'title': '',
                        'number': hymn_info,
                        'verses': [],
                        'author': '',
                        'category': '',
                        'language': 'English',
                    }
                    number_found = True
                    title_found = False
                current_verse = None
                verse_number = 1
                continue
            
            # If we don't have a current hymn yet, start one
            if not current_hymn:
                current_hymn = {
                    'title': '',
                    'number': None,
                    'verses': [],
                    'author': '',
                    'category': '',
                    'language': 'English',
                }
            
            # Try to extract hymn number from patterns (if not found yet)
            if not number_found:
                is_new, hymn_info = is_new_hymn_start(text)
                if is_new:
                    if isinstance(hymn_info, tuple):
                        current_hymn['number'] = hymn_info[0]
                        current_hymn['title'] = hymn_info[1]
                        title_found = True
                    else:
                        current_hymn['number'] = hymn_info
                    number_found = True
                    continue
            
            # Try to extract title from first non-number paragraph
            if not title_found and number_found:
                # If we have a number but no title, use first non-verse line as title
                if not re.match(r'^(\d+)\.', text):
                    current_hymn['title'] = text
                    title_found = True
                    continue
            
            # If we still don't have a title and this is the first content, use it as title
            if not title_found:
                verse_match = re.match(r'^(\d+)\.', text)
                if verse_match:
                    # Use first few words of first verse as title if no title found
                    verse_text = re.sub(r'^\d+\.\s*', '', text)
                    current_hymn['title'] = verse_text[:50].strip()
                    if len(verse_text) > 50:
                        current_hymn['title'] += '...'
                    title_found = True
                    # Continue to process this as a verse below
                else:
                    current_hymn['title'] = text
                    title_found = True
                    continue
            
            # Check if it's a verse number or chorus
            verse_match = re.match(r'^(\d+)\.', text)
            chorus_match = re.match(r'^(Chorus|Refrain):?', text, re.IGNORECASE)
            
            if verse_match:
                # Save previous verse if exists
                if current_verse:
                    current_hymn['verses'].append(current_verse)
                
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
                    current_hymn['verses'].append(current_verse)
                
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
        
        # Save last hymn
        if current_hymn:
            save_current_hymn()
        
        # If no hymns found, return single hymn (backward compatibility)
        if not all_hymns:
            return {
                'title': '',
                'number': None,
                'verses': [],
                'author': '',
                'category': '',
                'language': 'English',
            }
        
        # If only one hymn, return it directly (backward compatibility)
        if len(all_hymns) == 1:
            return all_hymns[0]
        
        # Return list of hymns
        return all_hymns
    except Exception as e:
        raise Exception(f"Error parsing Word document: {str(e)}")


def parse_text_file(file):
    """Parse plain text file and extract hymn data - supports multiple hymns in one document"""
    try:
        # Reset file pointer in case it was read before
        file.seek(0)
        content = file.read().decode('utf-8')
        lines = content.split('\n')
        
        all_hymns = []
        
        current_hymn = None
        current_verse = None
        verse_number = 1
        title_found = False
        number_found = False
        blank_lines_count = 0
        
        def save_current_hymn():
            """Save the current hymn if it has data"""
            nonlocal current_hymn, current_verse, verse_number, title_found, number_found
            if current_hymn and (current_hymn.get('number') is not None or current_hymn.get('verses')):
                # Add last verse
                if current_verse:
                    current_hymn['verses'].append(current_verse)
                    current_verse = None
                # Only add if it has verses or a valid number
                if current_hymn.get('verses') or current_hymn.get('number'):
                    all_hymns.append(current_hymn)
            # Reset for next hymn
            current_hymn = {
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
        
        def is_new_hymn_start(text):
            """Check if this line indicates a new hymn"""
            # Skip header lines (like "THE NEW CATHOLIC HYMNAL, 2021")
            if re.match(r'^THE\s+NEW\s+CATHOLIC\s+HYMNAL', text, re.IGNORECASE):
                return False, None
            
            # Pattern 1: "NCH 1", "OCH 2", etc. (prefix + number)
            prefix_match = re.match(r'^[A-Z]{2,}\s+(\d+)$', text)
            if prefix_match:
                return True, int(prefix_match.group(1))
            
            # Pattern 2: "101. Amazing Grace" or "1. Amazing Grace"
            title_match = re.match(r'^(\d+)\.\s*(.+)$', text)
            if title_match:
                return True, (int(title_match.group(1)), title_match.group(2))
            
            # Pattern 3: Just a number "101" or "1" (but only if we're starting fresh or after a hymn with verses)
            number_only_match = re.match(r'^(\d+)$', text)
            if number_only_match:
                # Only treat as new hymn if:
                # 1. We don't have a current hymn yet, OR
                # 2. Current hymn has verses (meaning we've finished it), OR
                # 3. Current hymn has a number and this is a different number
                if not current_hymn:
                    return True, int(number_only_match.group(1))
                elif current_hymn.get('verses'):
                    return True, int(number_only_match.group(1))
                elif current_hymn.get('number') and int(number_only_match.group(1)) != current_hymn.get('number'):
                    return True, int(number_only_match.group(1))
            
            return False, None
        
        for line in lines:
            text = line.strip()
            
            # Track blank lines
            if not text:
                blank_lines_count += 1
                # Multiple blank lines might indicate hymn separation
                if blank_lines_count >= 2 and current_hymn and current_hymn.get('verses'):
                    # Save current hymn if it has verses
                    save_current_hymn()
                    blank_lines_count = 0
                continue
            else:
                blank_lines_count = 0
            
            # Skip header lines
            if re.match(r'^THE\s+NEW\s+CATHOLIC\s+HYMNAL', text, re.IGNORECASE):
                continue
            
            # Check if this is a new hymn start
            is_new, hymn_info = is_new_hymn_start(text)
            if is_new:
                # Save previous hymn if exists and has verses
                if current_hymn and current_hymn.get('verses'):
                    save_current_hymn()
                
                # Start new hymn
                if isinstance(hymn_info, tuple):
                    # Pattern 2: number and title together
                    current_hymn = {
                        'title': hymn_info[1],
                        'number': hymn_info[0],
                        'verses': [],
                        'author': '',
                        'category': '',
                        'language': 'English',
                    }
                    number_found = True
                    title_found = True
                else:
                    # Pattern 1 or 3: just number
                    current_hymn = {
                        'title': '',
                        'number': hymn_info,
                        'verses': [],
                        'author': '',
                        'category': '',
                        'language': 'English',
                    }
                    number_found = True
                    title_found = False
                current_verse = None
                verse_number = 1
                continue
            
            # If we don't have a current hymn yet, start one
            if not current_hymn:
                current_hymn = {
                    'title': '',
                    'number': None,
                    'verses': [],
                    'author': '',
                    'category': '',
                    'language': 'English',
                }
            
            # Try to extract hymn number from patterns (if not found yet)
            if not number_found:
                is_new, hymn_info = is_new_hymn_start(text)
                if is_new:
                    if isinstance(hymn_info, tuple):
                        current_hymn['number'] = hymn_info[0]
                        current_hymn['title'] = hymn_info[1]
                        title_found = True
                    else:
                        current_hymn['number'] = hymn_info
                    number_found = True
                    continue
            
            # Try to extract title from first non-number line
            if not title_found and number_found:
                # If we have a number but no title, use first non-verse line as title
                if not re.match(r'^(\d+)\.', text):
                    current_hymn['title'] = text
                    title_found = True
                    continue
            
            # If we still don't have a title and this is the first content, use it as title
            if not title_found:
                verse_match = re.match(r'^(\d+)\.', text)
                if verse_match:
                    # Use first few words of first verse as title if no title found
                    verse_text = re.sub(r'^\d+\.\s*', '', text)
                    current_hymn['title'] = verse_text[:50].strip()
                    if len(verse_text) > 50:
                        current_hymn['title'] += '...'
                    title_found = True
                    # Continue to process this as a verse below
                else:
                    current_hymn['title'] = text
                    title_found = True
                    continue
            
            # Check if it's a verse number or chorus
            verse_match = re.match(r'^(\d+)\.', text)
            chorus_match = re.match(r'^(Chorus|Refrain):?', text, re.IGNORECASE)
            
            if verse_match:
                if current_verse:
                    current_hymn['verses'].append(current_verse)
                
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
                    current_hymn['verses'].append(current_verse)
                
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
        
        # Save last hymn
        if current_hymn:
            save_current_hymn()
        
        # If no hymns found, return single hymn (backward compatibility)
        if not all_hymns:
            return {
                'title': '',
                'number': None,
                'verses': [],
                'author': '',
                'category': '',
                'language': 'English',
            }
        
        # If only one hymn, return it directly (backward compatibility)
        if len(all_hymns) == 1:
            return all_hymns[0]
        
        # Return list of hymns
        return all_hymns
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

