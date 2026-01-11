"""
URL configuration for Nova Hymnal Backend project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger Schema View
schema_view = get_schema_view(
    openapi.Info(
        title="Nova Hymnal Premium API",
        default_version='v1',
        description="""
        Complete REST API for Nova Hymnal Premium mobile application.
        
        ## Features
        - **Authentication**: JWT-based authentication for secure access
        - **Hymns**: Browse, search, and filter hymns with full details
        - **Premium Content**: Sheet music and audio files (premium subscription required)
        - **User Features**: Favorites, playlists, and notes
        - **Subscriptions**: Manage premium subscriptions
        
        ## Authentication
        To authenticate, use the `/api/v1/auth/login/` endpoint to get JWT tokens.
        Then include the token in the Authorization header:
        ```
        Authorization: Bearer {your_token_here}
        ```
        
        ## Premium Features
        Premium features require an active subscription. Free users have limited access:
        - Free: 10 favorites maximum
        - Premium: Unlimited favorites, sheet music, audio files, and more
        """,
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@novahymnal.com"),
        license=openapi.License(name="Private License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('hymns.urls')),
    
    # Swagger/OpenAPI Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),  # Alias for convenience
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

