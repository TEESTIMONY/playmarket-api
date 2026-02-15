"""
URL configuration for playmarket project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import os
from bounties.views import serve_auction_image

urlpatterns = [
    path('admin/', admin.site.urls),
    path('bounties/', include('bounties.urls')),
    path('api/', include('bounties.api_urls')),  # Include API endpoints
    # Legacy-friendly auction image route (handles Django auto-renamed files)
    path('media/auction_images/<path:filename>', serve_auction_image, name='serve_auction_image'),
]

# Serve uploaded media files.
#
# In production on Render, DEBUG=False means Django's `static()` helper will
# not add media routes unless `insecure=True` is provided. Without this,
# auction image URLs return 404 in live environments.
urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT,
    insecure=not settings.DEBUG,
)

# Backward compatibility for legacy image URLs stored as /auction_images/...
urlpatterns += static(
    '/auction_images/',
    document_root=os.path.join(settings.MEDIA_ROOT, 'auction_images'),
    insecure=not settings.DEBUG,
)
