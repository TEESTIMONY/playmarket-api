from django.urls import path
from .api_views import UserClaimedBountiesView, user_claimed_bounties_stats
from .auth_views import firebase_login, verify_token, logout, get_user_profile
from .views import (
    UserBalanceView, UserTransactionsView, AdminUserBalanceAdjustmentView,
    UserDetailView, UserListView, BountyClaimApprovalView, PointTransferView,
    AdminBountyClaimsView,
)
from .auction_views import (
    AuctionListView, AuctionDetailView, CreateAuctionView, DeleteAuctionView, PlaceBidView,
    AuctionStatusView, EndAuctionView, AuctionLeaderboardView,
    UserAuctionHistoryView
)

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', firebase_login, name='firebase_login'),
    path('auth/verify/', verify_token, name='verify_token'),
    path('auth/logout/', logout, name='logout'),
    path('auth/profile/', get_user_profile, name='get_user_profile'),
    
    # API endpoints for claimed bounties
    path('user/<str:user_id>/claimed-bounties/', UserClaimedBountiesView.as_view(), name='user_claimed_bounties'),
    path('user/<str:user_id>/claimed-bounties/stats/', user_claimed_bounties_stats, name='user_claimed_bounties_stats'),
    
    # User endpoints
    path('bounties/balance/', UserBalanceView.as_view(), name='user_balance'),
    path('bounties/transactions/', UserTransactionsView.as_view(), name='user_transactions'),
    path('bounties/point-transfers/', PointTransferView.as_view(), name='user_point_transfers'),
    path('bounties/profile/', UserDetailView.as_view(), name='user_profile'),
    
    # Admin endpoints
    path('bounties/admin/users/', UserListView.as_view(), name='admin_users'),
    path('bounties/admin/adjust-balance/', AdminUserBalanceAdjustmentView.as_view(), name='admin_adjust_balance'),
    path('bounties/admin/bounty-claims/', AdminBountyClaimsView.as_view(), name='admin_bounty_claims'),
    path('bounties/claims/<int:claim_id>/approve/', BountyClaimApprovalView.as_view(), name='approve_bounty_claim'),
    
    # Auction endpoints
    path('auctions/', AuctionListView.as_view(), name='auction_list'),
    path('auctions/<int:id>/', AuctionDetailView.as_view(), name='auction_detail'),
    path('auctions/create/', CreateAuctionView.as_view(), name='create_auction'),
    path('auctions/<int:auction_id>/delete/', DeleteAuctionView.as_view(), name='delete_auction'),
    path('auctions/<int:auction_id>/bid/', PlaceBidView.as_view(), name='place_bid'),
    path('auctions/<int:auction_id>/status/', AuctionStatusView.as_view(), name='auction_status'),
    path('auctions/<int:auction_id>/end/', EndAuctionView.as_view(), name='end_auction'),
    path('auctions/<int:auction_id>/leaderboard/', AuctionLeaderboardView.as_view(), name='auction_leaderboard'),
    path('auctions/history/', UserAuctionHistoryView.as_view(), name='user_auction_history'),
]
