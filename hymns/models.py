from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.exceptions import ValidationError


class Category(models.Model):
    """Category model for organizing hymns"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Author(models.Model):
    """Author model for hymn authors"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    biography = models.TextField(blank=True, null=True)
    birth_year = models.IntegerField(blank=True, null=True)
    death_year = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Denomination(models.Model):
    """Denomination model for church denominations"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0, help_text="Order for display in UI")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = "Denominations"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class DenominationHymn(models.Model):
    """Junction table linking hymns to denominations with denomination-specific data"""
    HYMN_PERIOD_CHOICES = [
        ('new', 'New'),
        ('old', 'Old'),
    ]
    
    hymn = models.ForeignKey('Hymn', on_delete=models.CASCADE, related_name='denomination_hymns')
    denomination = models.ForeignKey(Denomination, on_delete=models.CASCADE, related_name='hymns')
    number = models.IntegerField(validators=[MinValueValidator(1)], help_text="Hymn number in this denomination/period")
    hymn_period = models.CharField(
        max_length=10,
        choices=HYMN_PERIOD_CHOICES,
        null=True,
        blank=True,
        help_text="Required for Catholic hymns. Old and New have separate numbering sequences."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [('denomination', 'hymn_period', 'number')]
        ordering = ['denomination', 'hymn_period', 'number']
        indexes = [
            models.Index(fields=['denomination', 'hymn_period', 'number']),
            models.Index(fields=['denomination', 'hymn_period']),
        ]
        verbose_name = "Denomination Hymn"
        verbose_name_plural = "Denomination Hymns"
    
    def clean(self):
        """Validate that Catholic hymns must have hymn_period"""
        if self.denomination and self.denomination.slug == 'catholic':
            if not self.hymn_period:
                raise ValidationError("Catholic hymns must specify hymn_period (new or old)")
        elif self.hymn_period:
            raise ValidationError("hymn_period can only be set for Catholic hymns")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        period_str = f" ({self.get_hymn_period_display()})" if self.hymn_period else ""
        return f"{self.denomination.name}{period_str} #{self.number}: {self.hymn.title}"


class Hymn(models.Model):
    """Main Hymn model - hymns can belong to multiple denominations with different numbers"""
    # REMOVED: number field (now stored in DenominationHymn)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, blank=True, related_name='hymns')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='hymns')
    language = models.CharField(max_length=50, default='English')
    
    # Denominations - ManyToMany through DenominationHymn
    denominations = models.ManyToManyField(
        Denomination,
        through='DenominationHymn',
        related_name='hymn_set',
        blank=True,
        help_text="Hymns can belong to multiple denominations with different numbers"
    )
    
    # Hymn content (shared across denominations)
    scripture_references = models.JSONField(default=list, blank=True, help_text="List of scripture references")
    history = models.TextField(blank=True, null=True, help_text="Historical background of the hymn")
    meter = models.CharField(max_length=50, blank=True, null=True)
    key_signature = models.CharField(max_length=10, blank=True, null=True)
    time_signature = models.CharField(max_length=10, blank=True, null=True)
    
    # Metadata
    is_premium = models.BooleanField(default=False, help_text="Requires premium subscription")
    is_featured = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['title']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Verse(models.Model):
    """Verse model for hymn verses - lyrics are denomination-specific!"""
    denomination_hymn = models.ForeignKey(
        DenominationHymn,
        on_delete=models.CASCADE,
        related_name='verses',
        help_text="Verses are linked to a specific denomination/period combination"
    )
    verse_number = models.IntegerField(validators=[MinValueValidator(1)])
    is_chorus = models.BooleanField(default=False)
    text = models.TextField(help_text="Lyrics can vary by denomination (e.g., 'You' vs 'Thou')")
    order = models.IntegerField(default=0, help_text="Order of verse in hymn")
    
    class Meta:
        ordering = ['order', 'verse_number']
        unique_together = ['denomination_hymn', 'verse_number', 'is_chorus']
    
    @property
    def hymn(self):
        """Convenience property to access the hymn"""
        return self.denomination_hymn.hymn
    
    @property
    def denomination(self):
        """Convenience property to access the denomination"""
        return self.denomination_hymn.denomination

    def __str__(self):
        verse_type = "Chorus" if self.is_chorus else f"Verse {self.verse_number}"
        period_str = f" ({self.denomination_hymn.get_hymn_period_display()})" if self.denomination_hymn.hymn_period else ""
        return f"{self.denomination_hymn.hymn.title} - {self.denomination_hymn.denomination.name}{period_str} - {verse_type}"


class SheetMusic(models.Model):
    """Sheet music model for hymns - supports both file upload and URL"""
    hymn = models.OneToOneField(Hymn, on_delete=models.CASCADE, related_name='sheet_music')
    file = models.FileField(upload_to='sheet_music/%Y/%m/%d/', blank=True, null=True, help_text="Upload PDF file")
    url = models.URLField(max_length=500, blank=True, null=True, help_text="Or provide external URL (e.g., Google Drive, Dropbox)")
    thumbnail = models.ImageField(upload_to='sheet_music/thumbnails/%Y/%m/%d/', blank=True, null=True)
    thumbnail_url = models.URLField(max_length=500, blank=True, null=True, help_text="Thumbnail URL if using external URL")
    page_count = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    is_premium = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Sheet Music"
    
    def clean(self):
        if not self.file and not self.url:
            raise ValidationError("Either file or URL must be provided")
        if self.file and self.url:
            raise ValidationError("Cannot provide both file and URL. Choose one.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Sheet Music - {self.hymn.title}"


class AudioFile(models.Model):
    """Audio file model for hymn audio"""
    AUDIO_TYPES = [
        ('piano', 'Piano Accompaniment'),
        ('soprano', 'Soprano'),
        ('alto', 'Alto'),
        ('tenor', 'Tenor'),
        ('bass', 'Bass'),
        ('full', 'Full Choir'),
    ]
    
    hymn = models.ForeignKey(Hymn, on_delete=models.CASCADE, related_name='audio_files')
    audio_type = models.CharField(max_length=20, choices=AUDIO_TYPES)
    file = models.FileField(upload_to='audio/%Y/%m/%d/')
    duration = models.IntegerField(blank=True, null=True, help_text="Duration in seconds")
    bitrate = models.IntegerField(blank=True, null=True, help_text="Bitrate in kbps")
    is_premium = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['hymn', 'audio_type']
        ordering = ['hymn', 'audio_type']

    def __str__(self):
        return f"{self.hymn.title} - {self.get_audio_type_display()}"


# User and Subscription Models

class User(AbstractUser):
    """Custom user model extending Django's AbstractUser"""
    email = models.EmailField(unique=True)
    device_id = models.CharField(max_length=255, blank=True, null=True, help_text="Mobile device identifier")
    platform = models.CharField(max_length=20, choices=[('ios', 'iOS'), ('android', 'Android'), ('web', 'Web')], blank=True, null=True)
    is_premium = models.BooleanField(default=False, help_text="Premium subscription status")
    premium_expires_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_premium']),
        ]
    
    def __str__(self):
        return self.username or self.email
    
    @property
    def has_active_premium(self):
        """Check if user has active premium subscription"""
        if not self.is_premium:
            return False
        if self.premium_expires_at and self.premium_expires_at < timezone.now():
            return False
        return True


class Subscription(models.Model):
    """Subscription model for premium subscriptions"""
    SUBSCRIPTION_STATUS = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending'),
    ]
    
    SUBSCRIPTION_TYPE = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('lifetime', 'Lifetime'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_TYPE, default='monthly')
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='pending')
    
    # In-app purchase identifiers
    product_id = models.CharField(max_length=255, help_text="Product ID from app store")
    transaction_id = models.CharField(max_length=255, unique=True, blank=True, null=True, help_text="Transaction ID from app store")
    original_transaction_id = models.CharField(max_length=255, blank=True, null=True, help_text="Original transaction ID for subscriptions")
    
    # Subscription dates
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    
    # Platform info
    platform = models.CharField(max_length=20, choices=[('ios', 'iOS'), ('android', 'Android')], blank=True, null=True)
    
    # Receipt data (for verification)
    receipt_data = models.TextField(blank=True, null=True, help_text="Receipt data from app store")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_subscription_type_display()} ({self.status})"
    
    def clean(self):
        if self.status == 'active' and self.expires_at and self.expires_at < timezone.now():
            raise ValidationError("Active subscription cannot have expired date")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
        # Update user's premium status
        if self.status == 'active' and self.user:
            self.user.is_premium = True
            self.user.premium_expires_at = self.expires_at
            self.user.save(update_fields=['is_premium', 'premium_expires_at'])
        elif self.status in ['expired', 'cancelled']:
            # Check if user has other active subscriptions
            has_other_active = Subscription.objects.filter(
                user=self.user,
                status='active'
            ).exclude(id=self.id).exists()
            
            if not has_other_active:
                self.user.is_premium = False
                self.user.premium_expires_at = None
                self.user.save(update_fields=['is_premium', 'premium_expires_at'])


class Favorite(models.Model):
    """User favorites for hymns"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    hymn = models.ForeignKey(Hymn, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'hymn']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.hymn.title}"


class Playlist(models.Model):
    """User playlists for hymns"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    hymns = models.ManyToManyField(Hymn, through='PlaylistHymn', related_name='playlists')
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"


class PlaylistHymn(models.Model):
    """Through model for playlist-hymn relationship with ordering"""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    hymn = models.ForeignKey(Hymn, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['playlist', 'hymn']
        ordering = ['order', 'added_at']
    
    def __str__(self):
        return f"{self.playlist.name} - {self.hymn.title}"


class HymnNote(models.Model):
    """User notes/annotations for hymns"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hymn_notes')
    hymn = models.ForeignKey(Hymn, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField()
    is_public = models.BooleanField(default=False, help_text="Allow other users to see this note")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'hymn']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.hymn.title} - Note"



