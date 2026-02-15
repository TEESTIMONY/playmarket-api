"""
WebSocket routing configuration for bounties app.

This file defines the URL patterns for WebSocket connections
and maps them to their respective consumers.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Test WebSocket endpoint for validation
    re_path(r'ws/test/$', consumers.TestConsumer.as_asgi()),
    
    # Auction WebSocket endpoints
    re_path(r'ws/auction/(?P<auction_id>\d+)/$', consumers.AuctionConsumer.as_asgi()),
    re_path(r'ws/auction/leaderboard/(?P<auction_id>\d+)/$', consumers.AuctionLeaderboardConsumer.as_asgi()),
    
    # General auction updates for all connected clients
    re_path(r'ws/auction/updates/$', consumers.AuctionUpdatesConsumer.as_asgi()),
]