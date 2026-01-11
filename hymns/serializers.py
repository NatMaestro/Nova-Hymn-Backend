from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import (
    Category, Author, Hymn, Verse, SheetMusic, AudioFile,
    User, Subscription, Favorite, Playlist, PlaylistHymn, HymnNote,
    Denomination, DenominationHymn
)


class CategorySerializer(serializers.ModelSerializer):
    hymn_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'hymn_count', 'created_at', 'updated_at']
        read_only_fields = ['slug', 'created_at', 'updated_at']

    def get_hymn_count(self, obj):
        return obj.hymns.count()


class AuthorSerializer(serializers.ModelSerializer):
    hymn_count = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = ['id', 'name', 'slug', 'biography', 'birth_year', 'death_year', 'hymn_count', 'created_at', 'updated_at']
        read_only_fields = ['slug', 'created_at', 'updated_at']

    def get_hymn_count(self, obj):
        return obj.hymns.count()


class DenominationSerializer(serializers.ModelSerializer):
    """Denomination serializer"""
    hymn_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Denomination
        fields = ['id', 'name', 'slug', 'description', 'is_active', 'display_order', 'hymn_count', 'created_at', 'updated_at']
        read_only_fields = ['slug', 'created_at', 'updated_at']
    
    def get_hymn_count(self, obj):
        return obj.hymns.count()


class DenominationHymnSerializer(serializers.ModelSerializer):
    """DenominationHymn serializer with hymn details"""
    hymn_title = serializers.CharField(source='hymn.title', read_only=True)
    denomination_name = serializers.CharField(source='denomination.name', read_only=True)
    verses = serializers.SerializerMethodField()
    
    class Meta:
        model = DenominationHymn
        fields = [
            'id', 'hymn', 'hymn_title', 'denomination', 'denomination_name',
            'number', 'hymn_period', 'verses', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_verses(self, obj):
        verses = obj.verses.all().order_by('order', 'verse_number')
        return VerseSerializer(verses, many=True).data


class VerseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Verse
        fields = ['id', 'verse_number', 'is_chorus', 'text', 'order']
        read_only_fields = ['id']


class HymnListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    author_name = serializers.CharField(source='author.name', read_only=True)
    # Denomination-specific number (from query param)
    number = serializers.SerializerMethodField()
    denomination_info = serializers.SerializerMethodField()

    class Meta:
        model = Hymn
        fields = [
            'id', 'number', 'title', 'slug', 'category', 'category_name',
            'author', 'author_name', 'language', 'is_premium', 'is_featured',
            'view_count', 'denomination_info', 'created_at'
        ]
        read_only_fields = ['slug', 'created_at']
    
    def get_number(self, obj):
        """Get denomination-specific number if denomination is provided in context"""
        request = self.context.get('request')
        if request:
            denomination_id = request.query_params.get('denomination')
            hymn_period = request.query_params.get('hymn_period')
            if denomination_id:
                try:
                    dh = obj.denomination_hymns.filter(denomination_id=denomination_id)
                    if hymn_period:
                        dh = dh.filter(hymn_period=hymn_period)
                    dh = dh.first()
                    if dh:
                        return dh.number
                except:
                    pass
        # Return first denomination number or None
        first_dh = obj.denomination_hymns.first()
        return first_dh.number if first_dh else None
    
    def get_denomination_info(self, obj):
        """Get all denomination associations"""
        dhs = obj.denomination_hymns.all()
        return [
            {
                'denomination_id': dh.denomination.id,
                'denomination_name': dh.denomination.name,
                'number': dh.number,
                'hymn_period': dh.hymn_period
            }
            for dh in dhs
        ]


class HymnDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for hymn detail view"""
    verses = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    author_name = serializers.CharField(source='author.name', read_only=True)
    author_biography = serializers.CharField(source='author.biography', read_only=True)
    sheet_music_url = serializers.SerializerMethodField()
    sheet_music_thumbnail = serializers.SerializerMethodField()
    audio_urls = serializers.SerializerMethodField()
    number = serializers.SerializerMethodField()
    denomination_info = serializers.SerializerMethodField()

    class Meta:
        model = Hymn
        fields = [
            'id', 'number', 'title', 'slug', 'category', 'category_name',
            'author', 'author_name', 'author_biography', 'language',
            'verses', 'scripture_references', 'history', 'meter',
            'key_signature', 'time_signature', 'is_premium', 'is_featured',
            'view_count', 'sheet_music_url', 'sheet_music_thumbnail',
            'audio_urls', 'denomination_info', 'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']
    
    def get_number(self, obj):
        """Get denomination-specific number if denomination is provided in context"""
        request = self.context.get('request')
        if request:
            denomination_id = request.query_params.get('denomination')
            hymn_period = request.query_params.get('hymn_period')
            if denomination_id:
                try:
                    dh = obj.denomination_hymns.filter(denomination_id=denomination_id)
                    if hymn_period:
                        dh = dh.filter(hymn_period=hymn_period)
                    dh = dh.first()
                    if dh:
                        return dh.number
                except:
                    pass
        # Return first denomination number or None
        first_dh = obj.denomination_hymns.first()
        return first_dh.number if first_dh else None
    
    def get_verses(self, obj):
        """Get denomination-specific verses if denomination is provided"""
        request = self.context.get('request')
        if request:
            denomination_id = request.query_params.get('denomination')
            hymn_period = request.query_params.get('hymn_period')
            if denomination_id:
                try:
                    dh = obj.denomination_hymns.filter(denomination_id=denomination_id)
                    if hymn_period:
                        dh = dh.filter(hymn_period=hymn_period)
                    dh = dh.first()
                    if dh:
                        verses = dh.verses.all().order_by('order', 'verse_number')
                        return VerseSerializer(verses, many=True).data
                except:
                    pass
        # Return first denomination's verses or empty
        first_dh = obj.denomination_hymns.first()
        if first_dh:
            verses = first_dh.verses.all().order_by('order', 'verse_number')
            return VerseSerializer(verses, many=True).data
        return []
    
    def get_denomination_info(self, obj):
        """Get all denomination associations"""
        dhs = obj.denomination_hymns.all()
        return [
            {
                'denomination_id': dh.denomination.id,
                'denomination_name': dh.denomination.name,
                'number': dh.number,
                'hymn_period': dh.hymn_period
            }
            for dh in dhs
        ]

    def get_sheet_music_url(self, obj):
        try:
            sheet_music = obj.sheet_music
            if sheet_music:
                # Check if URL is provided (external link)
                if sheet_music.url:
                    return sheet_music.url
                # Otherwise use file URL
                if sheet_music.file:
                    request = self.context.get('request')
                    if request:
                        return request.build_absolute_uri(sheet_music.file.url)
                    return sheet_music.file.url
        except SheetMusic.DoesNotExist:
            pass
        return None

    def get_sheet_music_thumbnail(self, obj):
        try:
            sheet_music = obj.sheet_music
            if sheet_music:
                # Check if thumbnail URL is provided (external link)
                if sheet_music.thumbnail_url:
                    return sheet_music.thumbnail_url
                # Otherwise use file thumbnail
                if sheet_music.thumbnail:
                    request = self.context.get('request')
                    if request:
                        return request.build_absolute_uri(sheet_music.thumbnail.url)
                    return sheet_music.thumbnail.url
        except SheetMusic.DoesNotExist:
            pass
        return None

    def get_audio_urls(self, obj):
        audio_files = obj.audio_files.all()
        audio_urls = {}
        request = self.context.get('request')
        
        for audio_file in audio_files:
            if audio_file.file:
                url = request.build_absolute_uri(audio_file.file.url) if request else audio_file.file.url
                audio_urls[audio_file.audio_type] = url
        
        return audio_urls if audio_urls else None


class SheetMusicSerializer(serializers.ModelSerializer):
    hymn_title = serializers.CharField(source='hymn.title', read_only=True)
    hymn_number = serializers.IntegerField(source='hymn.number', read_only=True)
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    url = serializers.URLField(required=False, allow_blank=True, help_text="External URL for sheet music")

    class Meta:
        model = SheetMusic
        fields = [
            'id', 'hymn', 'hymn_title', 'hymn_number', 'file', 'url', 'file_url',
            'thumbnail', 'thumbnail_url', 'page_count', 'is_premium',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_file_url(self, obj):
        # Return URL if provided, otherwise return file URL
        if obj.url:
            return obj.url
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

    def get_thumbnail_url(self, obj):
        # Return thumbnail URL if provided, otherwise return file thumbnail
        if obj.thumbnail_url:
            return obj.thumbnail_url
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None


class AudioFileSerializer(serializers.ModelSerializer):
    hymn_title = serializers.CharField(source='hymn.title', read_only=True)
    hymn_number = serializers.IntegerField(source='hymn.number', read_only=True)
    file_url = serializers.SerializerMethodField()
    audio_type_display = serializers.CharField(source='get_audio_type_display', read_only=True)

    class Meta:
        model = AudioFile
        fields = [
            'id', 'hymn', 'hymn_title', 'hymn_number', 'audio_type',
            'audio_type_display', 'file', 'file_url', 'duration', 'bitrate',
            'is_premium', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


# User and Subscription Serializers

class UserSerializer(serializers.ModelSerializer):
    """User serializer"""
    has_active_premium = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_premium', 'has_active_premium', 'premium_expires_at',
            'device_id', 'platform', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'is_premium', 'has_active_premium', 'premium_expires_at', 'date_joined', 'last_login']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm Password')
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 'device_id', 'platform']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer with user data"""
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        token['is_premium'] = user.has_active_premium
        return token


class SubscriptionSerializer(serializers.ModelSerializer):
    """Subscription serializer"""
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'user_id', 'subscription_type', 'status',
            'product_id', 'transaction_id', 'original_transaction_id',
            'started_at', 'expires_at', 'cancelled_at', 'platform',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'started_at', 'created_at', 'updated_at']


class FavoriteSerializer(serializers.ModelSerializer):
    """Favorite serializer"""
    user = UserSerializer(read_only=True)
    hymn = HymnListSerializer(read_only=True)
    hymn_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Favorite
        fields = ['id', 'user', 'hymn', 'hymn_id', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class PlaylistHymnSerializer(serializers.ModelSerializer):
    """Playlist hymn through model serializer"""
    hymn = HymnListSerializer(read_only=True)
    hymn_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = PlaylistHymn
        fields = ['id', 'hymn', 'hymn_id', 'order', 'added_at']
        read_only_fields = ['id', 'added_at']


class PlaylistSerializer(serializers.ModelSerializer):
    """Playlist serializer"""
    user = UserSerializer(read_only=True)
    hymns = PlaylistHymnSerializer(source='playlisthymn_set', many=True, read_only=True)
    hymn_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Playlist
        fields = [
            'id', 'user', 'name', 'description', 'hymns', 'hymn_count',
            'is_public', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_hymn_count(self, obj):
        return obj.hymns.count()


class HymnNoteSerializer(serializers.ModelSerializer):
    """Hymn note/annotation serializer"""
    user = UserSerializer(read_only=True)
    hymn = HymnListSerializer(read_only=True)
    hymn_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = HymnNote
        fields = [
            'id', 'user', 'hymn', 'hymn_id', 'title', 'content',
            'is_public', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

