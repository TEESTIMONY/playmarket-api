"""
ASGI config for playmarket project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import bounties.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playmarket.settings')

# Configure Django ASGI application
django_asgi_app = get_asgi_application()

# Configure Channels application with WebSocket support
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            bounties.routing.websocket_urlpatterns
        )
    ),
})