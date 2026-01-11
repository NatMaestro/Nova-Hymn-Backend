from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from .models import (
    Category, Author, Denomination, DenominationHymn, Hymn, Verse, SheetMusic, AudioFile,
    User, Subscription, Favorite, Playlist, PlaylistHymn, HymnNote
)
from .admin_actions import bulk_upload_hymns, parse_word_document, parse_text_file


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'hymn_count', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']

    def hymn_count(self, obj):
        return obj.hymns.count()
    hymn_count.short_description = 'Hymn Count'


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'birth_year', 'death_year', 'hymn_count', 'created_at']
    search_fields = ['name', 'biography']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']

    def hymn_count(self, obj):
        return obj.hymns.count()
    hymn_count.short_description = 'Hymn Count'


@admin.register(Denomination)
class DenominationAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'display_order', 'hymn_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Settings', {
            'fields': ('is_active', 'display_order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def hymn_count(self, obj):
        return obj.hymns.count()
    hymn_count.short_description = 'Hymn Count'


class VerseInline(admin.TabularInline):
    """Inline for verses - now linked to DenominationHymn"""
    model = Verse
    extra = 1
    fields = ['verse_number', 'is_chorus', 'text', 'order']  # denomination_hymn is auto-set
    ordering = ['order', 'verse_number']


@admin.register(DenominationHymn)
class DenominationHymnAdmin(admin.ModelAdmin):
    """Admin for managing denomination-hymn associations"""
    list_display = ['hymn', 'denomination', 'number', 'hymn_period', 'verse_count', 'created_at']
    list_filter = ['denomination', 'hymn_period', 'created_at']
    search_fields = ['hymn__title', 'denomination__name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [VerseInline]  # Add VerseInline to manage verses
    fieldsets = (
        ('Association', {
            'fields': ('hymn', 'denomination', 'number', 'hymn_period')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def verse_count(self, obj):
        return obj.verses.count()
    verse_count.short_description = 'Verses'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('bulk-upload/', self.admin_site.admin_view(self.bulk_upload_view), name='hymns_denominationhymn_bulk_upload'),
        ]
        return custom_urls + urls
    
    def bulk_upload_view(self, request):
        """Bulk upload denomination hymns with verses"""
        if request.method == 'POST':
            files = request.FILES.getlist('files')
            denomination_id = request.POST.get('denomination')
            hymn_period = request.POST.get('hymn_period') or None
            category_id = request.POST.get('category')
            author_id = request.POST.get('author')
            is_premium = request.POST.get('is_premium') == 'on'
            start_number = request.POST.get('start_number', '').strip()
            
            if not files:
                messages.error(request, 'Please select at least one file')
                return redirect('admin:hymns_denominationhymn_bulk_upload')
            
            if not denomination_id:
                messages.error(request, 'Please select a denomination')
                return redirect('admin:hymns_denominationhymn_bulk_upload')
            
            try:
                denomination = Denomination.objects.get(id=denomination_id)
            except Denomination.DoesNotExist:
                messages.error(request, 'Invalid denomination selected')
                return redirect('admin:hymns_denominationhymn_bulk_upload')
            
            # Validate hymn_period for Catholic
            if denomination.slug == 'catholic' and not hymn_period:
                messages.error(request, 'Catholic hymns must specify hymn period (New or Old)')
                return redirect('admin:hymns_denominationhymn_bulk_upload')
            elif denomination.slug != 'catholic' and hymn_period:
                messages.error(request, 'Hymn period can only be set for Catholic hymns')
                return redirect('admin:hymns_denominationhymn_bulk_upload')
            
            category = Category.objects.get(id=category_id) if category_id else None
            author = Author.objects.get(id=author_id) if author_id else None
            
            # Determine starting number
            if start_number:
                try:
                    current_number = int(start_number)
                except ValueError:
                    messages.error(request, 'Invalid starting number')
                    return redirect('admin:hymns_denominationhymn_bulk_upload')
            else:
                # Get the last number for this denomination/period
                last_dh = DenominationHymn.objects.filter(
                    denomination=denomination,
                    hymn_period=hymn_period
                ).order_by('-number').first()
                current_number = (last_dh.number + 1) if last_dh else 1
            
            created_count = 0
            error_count = 0
            
            from django.db import transaction
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
                        
                        # Get or create the Hymn (shared across denominations)
                        hymn, hymn_created = Hymn.objects.get_or_create(
                            title=hymn_data.get('title', 'Untitled Hymn'),
                            defaults={
                                'category': category,
                                'author': author,
                                'language': hymn_data.get('language', 'English'),
                                'is_premium': is_premium,
                            }
                        )
                        
                        # Create or get DenominationHymn
                        denomination_hymn, dh_created = DenominationHymn.objects.get_or_create(
                            hymn=hymn,
                            denomination=denomination,
                            hymn_period=hymn_period,
                            number=current_number,
                            defaults={}
                        )
                        
                        if dh_created:
                            # Add verses to this DenominationHymn
                            for verse_data in hymn_data.get('verses', []):
                                Verse.objects.create(
                                    denomination_hymn=denomination_hymn,
                                    verse_number=verse_data['verse_number'],
                                    is_chorus=verse_data.get('is_chorus', False),
                                    text=verse_data['text'],
                                    order=verse_data.get('order', verse_data['verse_number'])
                                )
                            created_count += 1
                            current_number += 1
                        else:
                            messages.warning(request, f'Denomination Hymn "{hymn.title}" #{current_number} already exists, skipped')
                            current_number += 1
                    
                    except Exception as e:
                        messages.error(request, f'Error processing {file.name}: {str(e)}')
                        error_count += 1
            
            messages.success(request, f'Successfully created {created_count} denomination hymns with verses. {error_count} errors.')
            return redirect('admin:hymns_denominationhymn_changelist')
        
        # GET request - show form
        denominations = Denomination.objects.filter(is_active=True)
        categories = Category.objects.all()
        authors = Author.objects.all()
        return render(request, 'admin/bulk_upload_denominationhymn.html', {
            'denominations': denominations,
            'categories': categories,
            'authors': authors,
            'title': 'Bulk Upload Denomination Hymns',
        })


class DenominationHymnInline(admin.TabularInline):
    """Inline for managing denomination associations and numbers"""
    model = DenominationHymn
    extra = 1
    fields = ['denomination', 'number', 'hymn_period']
    readonly_fields = []
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Customize formset if needed
        return formset


@admin.register(SheetMusic)
class SheetMusicAdmin(admin.ModelAdmin):
    list_display = ['hymn', 'has_file', 'has_url', 'page_count', 'is_premium', 'created_at']
    list_filter = ['is_premium', 'created_at']
    search_fields = ['hymn__title']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Hymn', {
            'fields': ('hymn',)
        }),
        ('File Upload', {
            'fields': ('file', 'thumbnail'),
            'description': 'Upload PDF file directly'
        }),
        ('External URL', {
            'fields': ('url', 'thumbnail_url'),
            'description': 'Or provide external URL (e.g., Google Drive, Dropbox). Note: Either file OR url should be provided, not both.'
        }),
        ('Metadata', {
            'fields': ('page_count', 'is_premium')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_file(self, obj):
        return bool(obj.file)
    has_file.boolean = True
    has_file.short_description = 'Has File'
    
    def has_url(self, obj):
        return bool(obj.url)
    has_url.boolean = True
    has_url.short_description = 'Has URL'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('bulk-upload/', self.admin_site.admin_view(self.bulk_upload_view), name='hymns_sheetmusic_bulk_upload'),
        ]
        return custom_urls + urls
    
    def bulk_upload_view(self, request):
        """Bulk upload sheet music via file uploads or URLs"""
        if request.method == 'POST':
            files = request.FILES.getlist('files')
            hymns_data = request.POST.get('hymns_data', '').strip()
            is_premium = request.POST.get('is_premium') == 'on'
            
            created_count = 0
            error_count = 0
            
            from django.db import transaction
            with transaction.atomic():
                # Handle file uploads
                if files:
                    for file in files:
                        try:
                            # Extract hymn number from filename
                            import re
                            filename = file.name
                            numbers = re.findall(r'\d+', filename)
                            
                            if not numbers:
                                messages.error(request, f'Could not extract hymn ID from filename: {filename}. Please use format: hymn-{id}.pdf')
                                error_count += 1
                                continue
                            
                            hymn_id = int(numbers[0])
                            
                            try:
                                hymn = Hymn.objects.get(id=hymn_id)
                            except Hymn.DoesNotExist:
                                messages.error(request, f'Hymn ID {hymn_id} not found')
                                error_count += 1
                                continue
                            
                            sheet_music, created = SheetMusic.objects.get_or_create(
                                hymn=hymn,
                                defaults={
                                    'file': file,
                                    'page_count': 1,
                                    'is_premium': is_premium,
                                }
                            )
                            
                            if created:
                                created_count += 1
                            else:
                                # Update existing
                                if not sheet_music.file:
                                    sheet_music.file = file
                                    sheet_music.save()
                                    created_count += 1
                                else:
                                    messages.warning(request, f'Sheet music for hymn "{hymn.title}" already has a file')
                        
                        except Exception as e:
                            messages.error(request, f'Error processing {file.name}: {str(e)}')
                            error_count += 1
                
                # Handle URL-based entries
                if hymns_data:
                    for line in hymns_data.split('\n'):
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        
                        try:
                            # Parse format: hymn_id|url|thumbnail_url|page_count
                            parts = line.split('|')
                            if len(parts) < 2:
                                continue
                            
                            hymn_id = parts[0].strip()
                            file_url = parts[1].strip()
                            thumbnail_url = parts[2].strip() if len(parts) > 2 else ''
                            page_count = int(parts[3].strip()) if len(parts) > 3 and parts[3].strip() else 1
                            
                            if not file_url.startswith('http'):
                                continue  # Skip non-URL entries (handled by file upload)
                            
                            try:
                                hymn = Hymn.objects.get(id=hymn_id)
                            except Hymn.DoesNotExist:
                                messages.error(request, f'Hymn ID {hymn_id} not found')
                                error_count += 1
                                continue
                            
                            sheet_music, created = SheetMusic.objects.get_or_create(
                                hymn=hymn,
                                defaults={
                                    'url': file_url,
                                    'thumbnail_url': thumbnail_url if thumbnail_url.startswith('http') else None,
                                    'page_count': page_count,
                                    'is_premium': is_premium,
                                }
                            )
                            
                            if created:
                                created_count += 1
                            else:
                                # Update existing if no URL
                                if not sheet_music.url:
                                    sheet_music.url = file_url
                                    if thumbnail_url.startswith('http'):
                                        sheet_music.thumbnail_url = thumbnail_url
                                    sheet_music.save()
                                    created_count += 1
                                else:
                                    messages.warning(request, f'Sheet music for hymn "{hymn.title}" already has a URL')
                        
                        except Exception as e:
                            messages.error(request, f'Error processing line: {str(e)}')
                            error_count += 1
            
            messages.success(request, f'Successfully created/updated {created_count} sheet music entries. {error_count} errors.')
            return redirect('admin:hymns_sheetmusic_changelist')
        
        hymns = Hymn.objects.all().order_by('title')[:100]  # Limit for display
        return render(request, 'admin/bulk_upload_sheetmusic.html', {
            'hymns': hymns,
            'title': 'Bulk Upload Sheet Music',
        })


@admin.register(AudioFile)
class AudioFileAdmin(admin.ModelAdmin):
    list_display = ['hymn', 'audio_type', 'duration', 'bitrate', 'is_premium', 'created_at']
    list_filter = ['audio_type', 'is_premium', 'created_at']
    search_fields = ['hymn__title']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Hymn', {
            'fields': ('hymn', 'audio_type')
        }),
        ('Audio File', {
            'fields': ('file',)
        }),
        ('Metadata', {
            'fields': ('duration', 'bitrate', 'is_premium')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('bulk-upload/', self.admin_site.admin_view(self.bulk_upload_view), name='hymns_audiofile_bulk_upload'),
        ]
        return custom_urls + urls
    
    def bulk_upload_view(self, request):
        """Bulk upload audio files"""
        if request.method == 'POST':
            files = request.FILES.getlist('files')
            audio_type = request.POST.get('audio_type')
            is_premium = request.POST.get('is_premium') == 'on'
            
            if not files or not audio_type:
                messages.error(request, 'Please select files and audio type')
                return redirect('admin:hymns_audiofile_bulk_upload')
            
            created_count = 0
            error_count = 0
            
            from django.db import transaction
            with transaction.atomic():
                for file in files:
                    try:
                        # Extract hymn number from filename (e.g., "101-piano.mp3" or "hymn_101_piano.mp3")
                        import re
                        filename = file.name
                        numbers = re.findall(r'\d+', filename)
                        
                        if not numbers:
                            messages.error(request, f'Could not extract hymn ID from filename: {filename}. Please use format: hymn-{id}-{type}.mp3')
                            error_count += 1
                            continue
                        
                        hymn_id = int(numbers[0])
                        
                        try:
                            hymn = Hymn.objects.get(id=hymn_id)
                        except Hymn.DoesNotExist:
                            messages.error(request, f'Hymn ID {hymn_id} not found')
                            error_count += 1
                            continue
                        
                        audio_file, created = AudioFile.objects.get_or_create(
                            hymn=hymn,
                            audio_type=audio_type,
                            defaults={
                                'file': file,
                                'is_premium': is_premium,
                            }
                        )
                        
                        if created:
                            created_count += 1
                        else:
                            messages.warning(request, f'Audio file for hymn "{hymn.title}" ({audio_type}) already exists')
                    
                    except Exception as e:
                        messages.error(request, f'Error processing {file.name}: {str(e)}')
                        error_count += 1
            
            messages.success(request, f'Successfully uploaded {created_count} audio files. {error_count} errors.')
            return redirect('admin:hymns_audiofile_changelist')
        
        hymns = Hymn.objects.all().order_by('title')
        from .models import AudioFile
        audio_types = AudioFile.AUDIO_TYPES
        return render(request, 'admin/bulk_upload_audio.html', {
            'hymns': hymns,
            'audio_types': audio_types,
            'title': 'Bulk Upload Audio Files',
        })


# User and Subscription Admin

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_premium', 'has_active_premium', 'premium_expires_at', 'date_joined']
    list_filter = ['is_premium', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['date_joined', 'last_login', 'premium_expires_at']
    fieldsets = (
        ('Authentication', {
            'fields': ('username', 'email', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name')
        }),
        ('Device Info', {
            'fields': ('device_id', 'platform')
        }),
        ('Premium Status', {
            'fields': ('is_premium', 'premium_expires_at', 'has_active_premium')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('date_joined', 'last_login')
        }),
    )
    
    def has_active_premium(self, obj):
        return obj.has_active_premium
    has_active_premium.boolean = True
    has_active_premium.short_description = 'Active Premium'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'subscription_type', 'status', 'platform', 'started_at', 'expires_at']
    list_filter = ['status', 'subscription_type', 'platform', 'started_at']
    search_fields = ['user__username', 'user__email', 'transaction_id', 'product_id']
    readonly_fields = ['started_at', 'created_at', 'updated_at']
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Subscription Details', {
            'fields': ('subscription_type', 'status', 'platform')
        }),
        ('App Store Info', {
            'fields': ('product_id', 'transaction_id', 'original_transaction_id', 'receipt_data')
        }),
        ('Dates', {
            'fields': ('started_at', 'expires_at', 'cancelled_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'hymn', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'hymn__title']
    readonly_fields = ['created_at']


class PlaylistHymnInline(admin.TabularInline):
    model = PlaylistHymn
    extra = 1
    fields = ['hymn', 'order']
    ordering = ['order']


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'hymn_count', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at']
    search_fields = ['name', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PlaylistHymnInline]
    
    def hymn_count(self, obj):
        return obj.hymns.count()
    hymn_count.short_description = 'Hymn Count'


@admin.register(HymnNote)
class HymnNoteAdmin(admin.ModelAdmin):
    list_display = ['hymn', 'user', 'title', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at']
    search_fields = ['hymn__title', 'user__username', 'title', 'content']
    readonly_fields = ['created_at', 'updated_at']


# Enhanced Hymn Admin with bulk upload
@admin.register(Hymn)
class HymnAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'author', 'language', 'get_denomination_list', 'is_premium', 'is_featured', 'view_count', 'created_at']
    list_filter = ['category', 'author', 'language', 'is_premium', 'is_featured', 'denominations', 'created_at']
    search_fields = ['title', 'author__name', 'category__name']
    readonly_fields = ['slug', 'view_count', 'created_at', 'updated_at']
    inlines = [DenominationHymnInline]
    # Note: Cannot use filter_horizontal with through model
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'category', 'author', 'language')
        }),
        ('Content', {
            'fields': ('scripture_references', 'history', 'meter', 'key_signature', 'time_signature')
        }),
        ('Metadata', {
            'fields': ('is_premium', 'is_featured', 'view_count')
        }),
        ('System Fields', {
            'fields': ('slug',),
            'classes': ('collapse',),
            'description': 'Auto-generated fields'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_denomination_list(self, obj):
        """Display denominations this hymn belongs to"""
        denoms = obj.denomination_hymns.all()
        if not denoms.exists():
            return "No denominations"
        return ", ".join([
            f"{dh.denomination.name}{' (' + dh.get_hymn_period_display() + ')' if dh.hymn_period else ''} #{dh.number}"
            for dh in denoms[:3]
        ]) + ("..." if denoms.count() > 3 else "")
    get_denomination_list.short_description = 'Denominations'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('bulk-upload/', self.admin_site.admin_view(self.bulk_upload_view), name='hymns_hymn_bulk_upload'),
        ]
        return custom_urls + urls
    
    def bulk_upload_view(self, request):
        """Custom view for bulk upload"""
        if request.method == 'POST':
            files = request.FILES.getlist('files')
            category_id = request.POST.get('category')
            author_id = request.POST.get('author')
            is_premium = request.POST.get('is_premium') == 'on'
            
            if not files:
                messages.error(request, 'Please select at least one file')
                return redirect('admin:hymns_hymn_bulk_upload')
            
            category = Category.objects.get(id=category_id) if category_id else None
            author = Author.objects.get(id=author_id) if author_id else None
            
            created_count = 0
            error_count = 0
            
            from django.db import transaction
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
                        
                        # Create hymn (without number - numbers are denomination-specific)
                        hymn, created = Hymn.objects.get_or_create(
                            title=hymn_data.get('title', 'Untitled Hymn'),
                            defaults={
                                'category': category,
                                'author': author,
                                'language': hymn_data.get('language', 'English'),
                                'is_premium': is_premium,
                            }
                        )
                        
                        if created:
                            # Note: Verses and denomination associations must be added separately
                            # through the admin interface or API
                            messages.info(request, f'Hymn "{hymn.title}" created. Please add denomination associations and verses manually.')
                            created_count += 1
                        else:
                            messages.warning(request, f'Hymn "{hymn.title}" already exists, skipped')
                    
                    except Exception as e:
                        messages.error(request, f'Error processing {file.name}: {str(e)}')
                        error_count += 1
            
            messages.success(request, f'Successfully created {created_count} hymns. {error_count} errors.')
            return redirect('admin:hymns_hymn_changelist')
        
        categories = Category.objects.all()
        authors = Author.objects.all()
        return render(request, 'admin/bulk_upload_hymns.html', {
            'categories': categories,
            'authors': authors,
            'title': 'Bulk Upload Hymns',
        })

