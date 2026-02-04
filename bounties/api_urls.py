from django.urls import path
from .api_views import UserClaimedBountiesView, user_claimed_bounties_stats

urlpatterns = [
    # API endpoints for claimed bounties
    path('api/user/<str:user_id>/claimed-bounties/', UserClaimedBountiesView.as_view(), name='user_claimed_bounties'),
    path('api/user/<str:user_id>/claimed-bounties/stats/', user_claimed_bounties_stats, name='user_claimed_bounties_stats'),
]