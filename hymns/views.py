from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from django_ratelimit.decorators import ratelimit
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import (
    Category, Author, Hymn, Verse, SheetMusic, AudioFile,
    User, Subscription, Favorite, Playlist, PlaylistHymn, HymnNote,
    Denomination, DenominationHymn
)
from .serializers import (
    CategorySerializer, AuthorSerializer, HymnListSerializer,
    HymnDetailSerializer, SheetMusicSerializer, AudioFileSerializer,
    UserSerializer, UserRegistrationSerializer, CustomTokenObtainPairSerializer,
    SubscriptionSerializer, FavoriteSerializer, PlaylistSerializer,
    PlaylistHymnSerializer, HymnNoteSerializer,
    DenominationSerializer, DenominationHymnSerializer
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class AuthorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing authors.
    """
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [AllowAny]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'biography']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class DenominationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing denominations.
    """
    queryset = Denomination.objects.filter(is_active=True)
    serializer_class = DenominationSerializer
    permission_classes = [AllowAny]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['display_order', 'name', 'created_at']
    ordering = ['display_order', 'name']


class DenominationHymnViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing denomination-specific hymns.
    """
    queryset = DenominationHymn.objects.select_related('hymn', 'denomination').prefetch_related('verses').all()
    serializer_class = DenominationHymnSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['denomination', 'hymn_period']
    search_fields = ['hymn__title', 'denomination__name']
    ordering_fields = ['number', 'created_at']
    ordering = ['denomination', 'hymn_period', 'number']


class HymnViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing hymns with premium content protection.
    Supports filtering by denomination and hymn_period.
    """
    queryset = Hymn.objects.select_related('category', 'author').prefetch_related(
        'denomination_hymns__denomination', 'denomination_hymns__verses', 'audio_files'
    ).all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'author', 'language', 'is_premium', 'is_featured']
    search_fields = ['title', 'author__name', 'category__name', 'denomination_hymns__denomination__name']
    ordering_fields = ['title', 'created_at', 'view_count']
    ordering = ['title']
    
    def get_queryset(self):
        """Filter hymns by denomination if provided"""
        queryset = super().get_queryset()
        denomination_id = self.request.query_params.get('denomination')
        hymn_period = self.request.query_params.get('hymn_period')
        
        if denomination_id:
            # Filter hymns that belong to this denomination
            queryset = queryset.filter(denomination_hymns__denomination_id=denomination_id)
            if hymn_period:
                queryset = queryset.filter(denomination_hymns__hymn_period=hymn_period)
            # Remove duplicates
            queryset = queryset.distinct()
        
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return HymnDetailSerializer
        return HymnListSerializer

    def retrieve(self, request, *args, **kwargs):
        """Increment view count when hymn is viewed"""
        instance = self.get_object()
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        
        # Check premium access for premium content
        user = request.user if request.user.is_authenticated else None
        has_premium = user.has_active_premium if user and hasattr(user, 'has_active_premium') else False
        
        serializer = self.get_serializer(instance, context={'request': request})
        data = serializer.data
        
        # Hide premium content if user doesn't have premium
        if not has_premium:
            # Remove sheet music and audio URLs for premium hymns
            if instance.is_premium or (instance.sheet_music and instance.sheet_music.is_premium):
                data['sheet_music_url'] = None
                data['sheet_music_thumbnail'] = None
            
            # Remove premium audio URLs
            if data.get('audio_urls'):
                premium_audio_types = ['piano', 'soprano', 'alto', 'tenor', 'bass', 'full']
                for audio_type in premium_audio_types:
                    # Check if audio file is premium
                    try:
                        audio_file = instance.audio_files.get(audio_type=audio_type)
                        if audio_file.is_premium:
                            data['audio_urls'].pop(audio_type, None)
                    except:
                        pass
                
                # Remove if empty
                if not data['audio_urls']:
                    data['audio_urls'] = None
        
        return Response(data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured hymns"""
        featured_hymns = self.queryset.filter(is_featured=True)
        page = self.paginate_queryset(featured_hymns)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(featured_hymns, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def daily(self, request):
        """Get hymn of the day (based on date)"""
        from datetime import date
        import hashlib
        
        # Generate consistent daily hymn based on date
        today = date.today().isoformat()
        hash_value = int(hashlib.md5(today.encode()).hexdigest(), 16)
        
        hymn_count = self.queryset.count()
        if hymn_count == 0:
            return Response({'detail': 'No hymns available'}, status=status.HTTP_404_NOT_FOUND)
        
        hymn_index = hash_value % hymn_count
        daily_hymn = self.queryset.all()[hymn_index]
        
        serializer = HymnDetailSerializer(daily_hymn, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def sheet_music(self, request, pk=None):
        """Get sheet music for a specific hymn (premium protected)"""
        hymn = self.get_object()
        user = request.user if request.user.is_authenticated else None
        has_premium = user.has_active_premium if user and hasattr(user, 'has_active_premium') else False
        
        try:
            sheet_music = hymn.sheet_music
            # Check premium access
            if sheet_music.is_premium and not has_premium:
                return Response(
                    {'detail': 'Premium subscription required to access sheet music'},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = SheetMusicSerializer(sheet_music, context={'request': request})
            return Response(serializer.data)
        except SheetMusic.DoesNotExist:
            return Response(
                {'detail': 'Sheet music not available for this hymn'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'], url_path='audio/(?P<audio_type>[^/.]+)')
    def audio(self, request, pk=None, audio_type=None):
        """Get audio file for a specific hymn and audio type (premium protected)"""
        hymn = self.get_object()
        user = request.user if request.user.is_authenticated else None
        has_premium = user.has_active_premium if user and hasattr(user, 'has_active_premium') else False
        
        valid_types = ['piano', 'soprano', 'alto', 'tenor', 'bass', 'full']
        if audio_type not in valid_types:
            return Response(
                {'detail': f'Invalid audio type. Must be one of: {", ".join(valid_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            audio_file = hymn.audio_files.get(audio_type=audio_type)
            # Check premium access
            if audio_file.is_premium and not has_premium:
                return Response(
                    {'detail': 'Premium subscription required to access audio'},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = AudioFileSerializer(audio_file, context={'request': request})
            return Response(serializer.data)
        except AudioFile.DoesNotExist:
            return Response(
                {'detail': f'{audio_type.capitalize()} audio not available for this hymn'},
                status=status.HTTP_404_NOT_FOUND
            )


class SheetMusicViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing sheet music library (premium protected).
    """
    queryset = SheetMusic.objects.select_related('hymn').all()
    serializer_class = SheetMusicSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_premium', 'hymn__category', 'hymn__language']
    search_fields = ['hymn__title', 'hymn__number']
    ordering_fields = ['created_at', 'hymn__number']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter premium content based on user subscription"""
        queryset = super().get_queryset()
        user = self.request.user if self.request.user.is_authenticated else None
        has_premium = user.has_active_premium if user else False
        
        if not has_premium:
            # Only show non-premium sheet music to free users
            queryset = queryset.filter(is_premium=False)
        
        return queryset


class AudioFileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audio files (premium protected).
    """
    queryset = AudioFile.objects.select_related('hymn').all()
    serializer_class = AudioFileSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['audio_type', 'is_premium', 'hymn__category']
    search_fields = ['hymn__title', 'hymn__number']
    ordering_fields = ['created_at', 'hymn__number']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter premium content based on user subscription"""
        queryset = super().get_queryset()
        user = self.request.user if self.request.user.is_authenticated else None
        has_premium = user.has_active_premium if user else False
        
        if not has_premium:
            # Only show non-premium audio to free users
            queryset = queryset.filter(is_premium=False)
        
        return queryset


# Authentication Views

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token view with user data"""
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response(
                {'detail': 'Unable to log in with provided credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get user from validated data
        user = serializer.user
        
        # Get tokens using the serializer's validate method
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        
        # Return response with tokens and user data
        from .serializers import UserSerializer
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='post',
    request_body=UserRegistrationSerializer,
    responses={
        201: openapi.Response('User created successfully', UserSerializer),
        400: 'Bad request - validation errors'
    },
    operation_description='Register a new user account',
    tags=['Authentication']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """User registration endpoint"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'user': UserSerializer(user).data,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response('User profile', UserSerializer),
        401: 'Unauthorized - authentication required'
    },
    operation_description='Get the current authenticated user profile',
    tags=['Authentication'],
    security=[{'Bearer': []}]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get current user profile"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


# Subscription Views

class SubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing subscriptions"""
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Users can only see their own subscriptions"""
        return Subscription.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Create subscription for current user"""
        serializer.save(user=self.request.user)
    
    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['transaction_id', 'product_id', 'receipt_data', 'platform'],
            properties={
                'transaction_id': openapi.Schema(type=openapi.TYPE_STRING, description='Transaction ID from app store'),
                'product_id': openapi.Schema(type=openapi.TYPE_STRING, description='Product ID (e.g., com.novahymnal.premium.monthly)'),
                'receipt_data': openapi.Schema(type=openapi.TYPE_STRING, description='Receipt data from app store'),
                'platform': openapi.Schema(type=openapi.TYPE_STRING, enum=['ios', 'android'], description='Platform (ios or android)'),
            }
        ),
        responses={
            200: openapi.Response('Subscription verified', SubscriptionSerializer),
            201: openapi.Response('Subscription created', SubscriptionSerializer),
            400: 'Bad request - missing required fields'
        },
        operation_description='Verify and create/update subscription from app store purchase receipt',
        tags=['Subscriptions'],
        security=[{'Bearer': []}]
    )
    @action(detail=False, methods=['post'])
    def verify(self, request):
        """Verify subscription from app store receipt"""
        transaction_id = request.data.get('transaction_id')
        product_id = request.data.get('product_id')
        receipt_data = request.data.get('receipt_data')
        platform = request.data.get('platform')
        
        if not all([transaction_id, product_id, receipt_data, platform]):
            return Response(
                {'detail': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if subscription already exists
        subscription, created = Subscription.objects.get_or_create(
            transaction_id=transaction_id,
            defaults={
                'user': request.user,
                'product_id': product_id,
                'receipt_data': receipt_data,
                'platform': platform,
                'status': 'active',
            }
        )
        
        if not created:
            # Update existing subscription
            subscription.receipt_data = receipt_data
            subscription.status = 'active'
            subscription.save()
        
        serializer = self.get_serializer(subscription)
        return Response(serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        method='get',
        responses={
            200: openapi.Response('Subscription status', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'has_premium': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'subscription': SubscriptionSerializer
                }
            ))
        },
        operation_description='Get the current user\'s subscription status',
        tags=['Subscriptions'],
        security=[{'Bearer': []}]
    )
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get current subscription status"""
        active_subscription = Subscription.objects.filter(
            user=request.user,
            status='active'
        ).first()
        
        if active_subscription:
            serializer = self.get_serializer(active_subscription)
            return Response({
                'has_premium': True,
                'subscription': serializer.data
            })
        
        return Response({
            'has_premium': False,
            'subscription': None
        })


# Favorites Views

class FavoriteViewSet(viewsets.ModelViewSet):
    """ViewSet for managing favorites"""
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Users can only see their own favorites"""
        return Favorite.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Create favorite for current user"""
        user = self.request.user
        hymn_id = serializer.validated_data.get('hymn_id')
        
        # Check favorite limit for free users
        if not user.has_active_premium:
            favorite_count = Favorite.objects.filter(user=user).count()
            if favorite_count >= 10:  # Free limit
                raise ValidationError("Free users can only save up to 10 favorites. Upgrade to Premium for unlimited favorites.")
        
        # Check if already favorited
        if Favorite.objects.filter(user=user, hymn_id=hymn_id).exists():
            raise ValidationError("Hymn is already in favorites")
        
        serializer.save(user=user)
    
    @action(detail=False, methods=['delete'])
    def remove(self, request):
        """Remove favorite by hymn ID"""
        hymn_id = request.data.get('hymn_id')
        if not hymn_id:
            return Response(
                {'detail': 'hymn_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        favorite = Favorite.objects.filter(user=request.user, hymn_id=hymn_id).first()
        if favorite:
            favorite.delete()
            return Response({'detail': 'Favorite removed'}, status=status.HTTP_200_OK)
        
        return Response(
            {'detail': 'Favorite not found'},
            status=status.HTTP_404_NOT_FOUND
        )


# Playlist Views

class PlaylistViewSet(viewsets.ModelViewSet):
    """ViewSet for managing playlists"""
    serializer_class = PlaylistSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Users can see their own playlists and public playlists"""
        user = self.request.user
        if user.has_active_premium:
            return Playlist.objects.filter(
                Q(user=user) | Q(is_public=True)
            )
        # Free users can only see their own playlists
        return Playlist.objects.filter(user=user)
    
    def perform_create(self, serializer):
        """Create playlist for current user"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_hymn(self, request, pk=None):
        """Add hymn to playlist"""
        playlist = self.get_object()
        hymn_id = request.data.get('hymn_id')
        
        if not hymn_id:
            return Response(
                {'detail': 'hymn_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            hymn = Hymn.objects.get(id=hymn_id)
            order = PlaylistHymn.objects.filter(playlist=playlist).count()
            PlaylistHymn.objects.get_or_create(
                playlist=playlist,
                hymn=hymn,
                defaults={'order': order}
            )
            return Response({'detail': 'Hymn added to playlist'}, status=status.HTTP_200_OK)
        except Hymn.DoesNotExist:
            return Response(
                {'detail': 'Hymn not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['delete'])
    def remove_hymn(self, request, pk=None):
        """Remove hymn from playlist"""
        playlist = self.get_object()
        hymn_id = request.data.get('hymn_id')
        
        if not hymn_id:
            return Response(
                {'detail': 'hymn_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        PlaylistHymn.objects.filter(playlist=playlist, hymn_id=hymn_id).delete()
        return Response({'detail': 'Hymn removed from playlist'}, status=status.HTTP_200_OK)


# Hymn Notes Views

class HymnNoteViewSet(viewsets.ModelViewSet):
    """ViewSet for managing hymn notes/annotations"""
    serializer_class = HymnNoteSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Users can see their own notes and public notes"""
        if self.request.user.is_authenticated:
            return HymnNote.objects.filter(
                Q(user=self.request.user) | Q(is_public=True)
            )
        return HymnNote.objects.filter(is_public=True)
    
    def perform_create(self, serializer):
        """Create note for current user"""
        serializer.save(user=self.request.user)

