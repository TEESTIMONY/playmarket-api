from django.urls import path
from . import views
from . import auction_views

app_name = 'bounties'

urlpatterns = [
    # Bounty endpoints
    path('', views.BountyListView.as_view(), name='bounty-list'),
    path('<int:pk>/', views.BountyDetailView.as_view(), name='bounty-detail'),
    path('<int:bounty_id>/claim/', views.BountyClaimView.as_view(), name='bounty-claim'),
    path('<int:bounty_id>/submit/', views.BountySubmitView.as_view(), name='bounty-submit'),
    path('claims/<int:claim_id>/approve/', views.BountyClaimApprovalView.as_view(), name='bounty-claim-approve'),
    path('my-claims/', views.UserBountyClaimsView.as_view(), name='user-claims'),
    
    # Redeem code endpoints
    path('redeem-codes/', views.RedeemCodeListView.as_view(), name='redeem-code-list'),
    path('redeem-codes/<int:pk>/', views.RedeemCodeDetailView.as_view(), name='redeem-code-detail'),
    path('redeem/', views.RedeemCodeRedeemView.as_view(), name='redeem-code-redeem'),
    
    # User endpoints
    path('balance/', views.UserBalanceView.as_view(), name='user-balance'),
    path('transactions/', views.UserTransactionsView.as_view(), name='user-transactions'),
    path('point-transfers/', views.PointTransferView.as_view(), name='point-transfers'),
    path('profile/', views.UserDetailView.as_view(), name='user-profile'),
    
    # Admin endpoints
    path('admin/users/', views.UserListView.as_view(), name='admin-users'),
    path('admin/adjust-balance/', views.AdminUserBalanceAdjustmentView.as_view(), name='admin-adjust-balance'),
    path('admin/bounty-claims/', views.AdminBountyClaimsView.as_view(), name='admin-bounty-claims'),
    
    # Auction endpoints
    path('auctions/', auction_views.AuctionListView.as_view(), name='auction-list'),
    path('auctions/<int:pk>/', auction_views.AuctionDetailView.as_view(), name='auction-detail'),
    path('auctions/create/', auction_views.CreateAuctionView.as_view(), name='auction-create'),
    path('auctions/<int:auction_id>/delete/', auction_views.DeleteAuctionView.as_view(), name='auction-delete'),
    path('auctions/<int:auction_id>/bid/', auction_views.PlaceBidView.as_view(), name='auction-bid'),
    path('auctions/<int:auction_id>/status/', auction_views.AuctionStatusView.as_view(), name='auction-status'),
    path('auctions/<int:auction_id>/end/', auction_views.EndAuctionView.as_view(), name='auction-end'),
    path('auctions/<int:auction_id>/leaderboard/', auction_views.AuctionLeaderboardView.as_view(), name='auction-leaderboard'),
    path('auctions/history/', auction_views.UserAuctionHistoryView.as_view(), name='auction-history'),
]
