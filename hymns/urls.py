from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CategoryViewSet, AuthorViewSet, HymnViewSet,
    SheetMusicViewSet, AudioFileViewSet,
    CustomTokenObtainPairView, register_user, user_profile,
    SubscriptionViewSet, FavoriteViewSet, PlaylistViewSet, HymnNoteViewSet,
    DenominationViewSet, DenominationHymnViewSet
)
from .webhooks import revenuecat_webhook

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'denominations', DenominationViewSet, basename='denomination')
router.register(r'denomination-hymns', DenominationHymnViewSet, basename='denominationhymn')
router.register(r'hymns', HymnViewSet, basename='hymn')
router.register(r'sheet-music', SheetMusicViewSet, basename='sheetmusic')
router.register(r'audio', AudioFileViewSet, basename='audio')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'favorites', FavoriteViewSet, basename='favorite')
router.register(r'playlists', PlaylistViewSet, basename='playlist')
router.register(r'notes', HymnNoteViewSet, basename='note')

urlpatterns = [
    path('', include(router.urls)),
    # Authentication
    path('auth/register/', register_user, name='register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', user_profile, name='user_profile'),
    # Webhooks
    path('webhooks/revenuecat/', revenuecat_webhook, name='revenuecat_webhook'),
]

