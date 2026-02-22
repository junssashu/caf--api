from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # API endpoints
    path('api/', include('accounts.urls')),
    path('api/', include('pdv.urls')),
    path('api/', include('recouvrements.urls')),
    path('api/', include('rapports.urls')),
    path('api/', include('core.urls')),
    # OpenAPI schema & docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
