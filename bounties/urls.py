from django.urls import path
from . import views

app_name = 'bounties'

urlpatterns = [
    path('', views.BountyListView.as_view(), name='bounty-list'),
    path('<int:pk>/', views.BountyDetailView.as_view(), name='bounty-detail'),
    path('<int:bounty_id>/claim/', views.BountyClaimView.as_view(), name='bounty-claim'),
    path('<int:bounty_id>/submit/', views.BountySubmitView.as_view(), name='bounty-submit'),
    path('claims/<int:claim_id>/approve/', views.BountyClaimApprovalView.as_view(), name='bounty-claim-approve'),
    path('my-claims/', views.UserBountyClaimsView.as_view(), name='user-claims'),
    path('redeem-codes/', views.RedeemCodeListView.as_view(), name='redeem-code-list'),
    path('redeem-codes/<int:pk>/', views.RedeemCodeDetailView.as_view(), name='redeem-code-detail'),
    path('redeem/', views.RedeemCodeRedeemView.as_view(), name='redeem-code-redeem'),
    path('balance/', views.UserBalanceView.as_view(), name='user-balance'),
    path('transactions/', views.UserTransactionsView.as_view(), name='user-transactions'),
    path('profile/', views.UserDetailView.as_view(), name='user-profile'),
    path('admin/users/', views.UserListView.as_view(), name='admin-users'),
    path('admin/adjust-balance/', views.AdminUserBalanceAdjustmentView.as_view(), name='admin-adjust-balance'),
]
