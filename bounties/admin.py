from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import path
from django.shortcuts import redirect, render
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.utils.html import format_html
from .models import UserProfile, CoinTransaction, Bounty, BountyClaim, RedeemCode, Auction, AuctionImage
from .auction_models import AuctionBid, AuctionWinner


# Inline for UserProfile in User admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = "User Profile"
    verbose_name_plural = "User Profiles"
    fields = ['coin_balance']
    readonly_fields = ['coin_balance']


# Inline for recent transactions in User admin
class RecentTransactionsInline(admin.TabularInline):
    model = CoinTransaction
    extra = 0
    fields = ['amount', 'transaction_type', 'description', 'created_at']
    readonly_fields = ['amount', 'transaction_type', 'description', 'created_at']
    ordering = ['-created_at']
    max_num = 5  # Show only last 5 transactions




@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'coin_balance', 'user_joined']
    list_filter = ['user__date_joined']
    search_fields = ['user__username', 'user__email']
    ordering = ['-user__date_joined']
    readonly_fields = ['user', 'coin_balance', 'user_joined']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'coin_balance')
        }),
        ('Timestamps', {
            'fields': ('user_joined',),
            'classes': ('collapse',)
        }),
    )
    
    def user_joined(self, obj):
        return obj.user.date_joined
    user_joined.short_description = 'Joined'
    user_joined.admin_order_field = 'user__date_joined'


@admin.register(CoinTransaction)
class CoinTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'transaction_type', 'description', 'reference_id', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__username', 'description', 'reference_id']
    ordering = ['-created_at']
    readonly_fields = ['user', 'amount', 'transaction_type', 'description', 'reference_id', 'created_at']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('user', 'amount', 'transaction_type', 'description', 'reference_id')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Bounty)
class BountyAdmin(admin.ModelAdmin):
    list_display = ['title', 'reward', 'status', 'claims_left', 'max_claims', 'expires_at', 'created_at']
    list_filter = ['status', 'created_at', 'expires_at']
    search_fields = ['title', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'claims_left']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'reward')
        }),
        ('Availability', {
            'fields': ('status', 'claims_left', 'max_claims', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('claims')


@admin.register(BountyClaim)
class BountyClaimAdmin(admin.ModelAdmin):
    list_display = ['bounty', 'user', 'status', 'submitted_at', 'approved_at', 'created_at']
    list_filter = ['status', 'created_at', 'submitted_at', 'approved_at']
    search_fields = ['bounty__title', 'user__username', 'submission']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'submitted_at', 'approved_at']

    fieldsets = (
        ('Claim Information', {
            'fields': ('bounty', 'user', 'status')
        }),
        ('Submission', {
            'fields': ('submission', 'submitted_at')
        }),
        ('Approval', {
            'fields': ('approved_at',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['approve_claims', 'reject_claims']

    def approve_claims(self, request, queryset):
        approved_count = 0
        for claim in queryset.filter(status='submitted'):
            # Award coins to user
            claim.user.profile.add_coins(
                claim.bounty.reward,
                'bounty_reward',
                claim.id,
                f"Bounty reward: {claim.bounty.title}"
            )
            claim.status = 'approved'
            claim.approved_at = timezone.now()
            claim.save()
            approved_count += 1
        
        self.message_user(request, f"Approved {approved_count} claims and awarded coins.")
    approve_claims.short_description = "Approve selected submitted claims and award coins"

    def reject_claims(self, request, queryset):
        queryset.filter(status__in=['pending', 'submitted']).update(status='rejected')
        self.message_user(request, f"Rejected {queryset.count()} claims.")
    reject_claims.short_description = "Reject selected claims"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('bounty', 'user')


@admin.register(RedeemCode)
class RedeemCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'coins', 'status', 'used_by', 'used_at', 'expires_at', 'created_at']
    list_filter = ['status', 'created_at', 'expires_at', 'used_at']
    search_fields = ['code', 'used_by__username']
    ordering = ['-created_at']
    readonly_fields = ['code', 'coins', 'status', 'used_by', 'used_at', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Code Information', {
            'fields': ('code', 'coins', 'status')
        }),
        ('Usage Details', {
            'fields': ('used_by', 'used_at')
        }),
        ('Expiration', {
            'fields': ('expires_at',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_codes', 'deactivate_codes']

    def activate_codes(self, request, queryset):
        updated = queryset.filter(status='expired').update(status='active')
        self.message_user(request, f"Activated {updated} expired codes.")
    activate_codes.short_description = "Activate selected expired codes"

    def deactivate_codes(self, request, queryset):
        updated = queryset.filter(status='active').update(status='expired')
        self.message_user(request, f"Deactivated {updated} active codes.")
    deactivate_codes.short_description = "Deactivate selected active codes"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('used_by')


# Custom inline to show user statistics in User admin
class UserStatisticsInline(admin.TabularInline):
    model = CoinTransaction
    extra = 0
    fields = []
    readonly_fields = []
    can_delete = False
    show_change_link = False
    
    def get_queryset(self, request):
        # Don't show individual transactions here, just use this for stats
        return CoinTransaction.objects.none()
    
    def get_extra(self, request, obj=None, **kwargs):
        return 0


# Inline for user's claimed bounties in User admin
class BountyClaimsInline(admin.TabularInline):
    model = BountyClaim
    extra = 0
    fields = ['bounty_info', 'status_display', 'reward', 'submitted_at', 'approved_at', 'view_claim']
    readonly_fields = ['bounty_info', 'status_display', 'reward', 'submitted_at', 'approved_at', 'view_claim']
    can_delete = False
    show_change_link = False
    ordering = ['-approved_at', '-created_at']
    
    def get_queryset(self, request):
        # Only show claims for the current user, ordered by approval date
        queryset = super().get_queryset(request)
        return queryset.select_related('bounty').order_by('-approved_at', '-created_at')
    
    def bounty_info(self, obj):
        """Display bounty title with ID"""
        return f"{obj.bounty.title} (ID: {obj.bounty.id})"
    bounty_info.short_description = "Bounty"
    
    def status_display(self, obj):
        """Display status with emoji and color"""
        status_badges = {
            'approved': ('✅', 'success'),
            'rejected': ('❌', 'danger'),
            'submitted': ('⏳', 'info'),
            'pending': ('⏳', 'warning')
        }
        
        emoji, badge_class = status_badges.get(obj.status, ('❓', 'secondary'))
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            badge_class,
            f"{emoji} {obj.get_status_display()}"
        )
    status_display.short_description = "Status"
    
    def reward(self, obj):
        """Display reward amount"""
        return f"{obj.bounty.reward} coins"
    reward.short_description = "Reward"
    
    def submitted_at(self, obj):
        """Display submission date"""
        if obj.submitted_at:
            return obj.submitted_at.strftime('%Y-%m-%d %H:%M')
        return "Not submitted"
    submitted_at.short_description = "Submitted"
    
    def approved_at(self, obj):
        """Display approval date"""
        if obj.approved_at:
            return obj.approved_at.strftime('%Y-%m-%d %H:%M')
        return "Not approved"
    approved_at.short_description = "Approved"
    
    def view_claim(self, obj):
        """Add a link to view the full claim"""
        return format_html(
            '<a href="{}" class="btn btn-sm btn-outline-primary">View/Edit</a>',
            f'/admin/bounties/bountyclaim/{obj.id}/change/'
        )
    view_claim.short_description = "Actions"


# Enhanced UserAdmin with statistics and overview functionality
class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline, RecentTransactionsInline, BountyClaimsInline]
    
    # Add coin balance to list display
    list_display = list(BaseUserAdmin.list_display) + ['coin_balance']
    
    def coin_balance(self, obj):
        try:
            return obj.profile.coin_balance
        except UserProfile.DoesNotExist:
            return 0
    coin_balance.short_description = 'Coins'
    coin_balance.admin_order_field = 'profile__coin_balance'
    
    # Add search for coin balance and transactions
    search_fields = BaseUserAdmin.search_fields + ('profile__coin_balance',)
    
    # Add custom methods to show statistics
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        
        if obj:  # Editing an existing user
            # Add statistics section
            stats_fieldset = ('User Statistics', {
                'fields': ('_total_earned', '_total_redeemed', '_net_balance', '_bounty_claims_count'),
                'classes': ('collapse',)
            })
            
            # Insert after the main user info section
            if len(fieldsets) > 1:
                fieldsets = fieldsets[:2] + (stats_fieldset,) + fieldsets[2:]
            else:
                fieldsets = fieldsets + (stats_fieldset,)
        
        return fieldsets
    
    def _total_earned(self, obj):
        total = CoinTransaction.objects.filter(
            user=obj, 
            transaction_type='bounty_reward'
        ).aggregate(total=Sum('amount'))['total'] or 0
        return f"{total} coins"
    _total_earned.short_description = "Total Earned"
    
    def _total_redeemed(self, obj):
        total = CoinTransaction.objects.filter(
            user=obj, 
            transaction_type='code_redemption'
        ).aggregate(total=Sum('amount'))['total'] or 0
        return f"{total} coins"
    _total_redeemed.short_description = "Total Redeemed"
    
    def _net_balance(self, obj):
        try:
            return f"{obj.profile.coin_balance} coins"
        except UserProfile.DoesNotExist:
            return "0 coins"
    _net_balance.short_description = "Net Balance"
    
    def _bounty_claims_count(self, obj):
        count = BountyClaim.objects.filter(user=obj).count()
        return count
    _bounty_claims_count.short_description = "Bounty Claims"
    
    def _claimed_bounties(self, obj):
        claims = BountyClaim.objects.filter(user=obj).select_related('bounty').order_by('-approved_at', '-created_at')
        if not claims:
            return "No bounties claimed"
        
        # Create a formatted list of claimed bounties
        bounty_list = []
        for claim in claims:
            status_badge = {
                'approved': '✅',
                'submitted': '⏳', 
                'pending': '⏳',
                'rejected': '❌'
            }.get(claim.status, '❓')
            
            bounty_info = f"{status_badge} {claim.bounty.title} ({claim.bounty.reward} coins)"
            bounty_list.append(bounty_info)
        
        return format_html('<br>'.join(bounty_list))
    _claimed_bounties.short_description = "Claimed Bounties"
    
    # Add custom methods to show detailed information
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:
            readonly_fields = readonly_fields + ('_total_earned', '_total_redeemed', '_net_balance', '_bounty_claims_count')
        return readonly_fields
    
    # Add a custom view for detailed user overview
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:user_id>/overview/', 
                 self.admin_site.admin_view(self.user_overview_view), 
                 name='user_overview'),
        ]
        return custom_urls + urls
    
    def user_overview_view(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('admin:auth_user_changelist')
        
        # Get user profile
        try:
            profile = user.profile
            coin_balance = profile.coin_balance
        except UserProfile.DoesNotExist:
            coin_balance = 0
        
        # Get recent transactions
        recent_transactions = CoinTransaction.objects.filter(user=user).order_by('-created_at')[:10]
        
        # Get user's bounty claims
        bounty_claims = BountyClaim.objects.filter(user=user).select_related('bounty').order_by('-approved_at', '-created_at')
        
        # Get used redeem codes
        used_codes = RedeemCode.objects.filter(used_by=user).order_by('-used_at')
        
        # Get statistics
        total_earned = CoinTransaction.objects.filter(
            user=user, 
            transaction_type='bounty_reward'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_redeemed = CoinTransaction.objects.filter(
            user=user, 
            transaction_type='code_redemption'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Debug: Print what we're getting
        print(f"User: {user.username}")
        print(f"Bounty claims count: {bounty_claims.count()}")
        for claim in bounty_claims:
            print(f"  - {claim.bounty.title} (ID: {claim.bounty.id}) - Status: {claim.status}")
        
        context = {
            'user': user,
            'coin_balance': coin_balance,
            'recent_transactions': recent_transactions,
            'bounty_claims': bounty_claims,
            'used_codes': used_codes,
            'total_earned': total_earned,
            'total_redeemed': total_redeemed,
            'title': f'User Overview: {user.username}',
        }
        
        return render(request, 'admin/user_overview.html', context)
    
    # Add custom action to view user overview
    def view_user_overview(self, request, queryset):
        if queryset.count() != 1:
            messages.error(request, "Please select exactly one user to view overview.")
            return
        
        user = queryset.first()
        return redirect('admin:user_overview', user_id=user.id)
    view_user_overview.short_description = "View User Overview"


# Auction Admin Classes

class AuctionImageInline(admin.TabularInline):
    model = AuctionImage
    extra = 0
    fields = ['image', 'order', 'created_at']
    readonly_fields = ['created_at']
    ordering = ['order', 'created_at']


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ['title', 'minimum_bid', 'current_highest_bid', 'current_highest_bidder', 'status', 'starts_at', 'ends_at', 'created_at']
    list_filter = ['status', 'starts_at', 'ends_at', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'current_highest_bid', 'current_highest_bidder', 'total_bids']
    inlines = [AuctionImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'minimum_bid')
        }),
        ('Images', {
            'fields': ('image_urls',),
            'description': 'Enter image URLs as a JSON array, e.g., ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]'
        }),
        ('Timing', {
            'fields': ('starts_at', 'ends_at')
        }),
        ('Status & Management', {
            'fields': ('status', 'created_by')
        }),
        ('Current State', {
            'fields': ('current_highest_bid', 'current_highest_bidder', 'total_bids'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_auctions', 'deactivate_auctions', 'end_auctions']

    def activate_auctions(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='active')
        self.message_user(request, f"Activated {updated} pending auctions.")
    activate_auctions.short_description = "Activate selected pending auctions"

    def deactivate_auctions(self, request, queryset):
        updated = queryset.filter(status='active').update(status='pending')
        self.message_user(request, f"Deactivated {updated} active auctions.")
    deactivate_auctions.short_description = "Deactivate selected active auctions"

    def end_auctions(self, request, queryset):
        # This would trigger the end auction logic
        ended_count = 0
        for auction in queryset.filter(status='active'):
            # Find highest bid
            highest_bid = AuctionBid.objects.filter(
                auction=auction,
                status='accepted'
            ).order_by('-amount').first()
            
            if highest_bid:
                # Create winner record
                AuctionWinner.objects.create(
                    auction=auction,
                    winner=highest_bid.user,
                    winning_amount=highest_bid.amount,
                    coins_transferred=False,
                )
                ended_count += 1
        
        if ended_count > 0:
            queryset.filter(status='active').update(status='ended')
            self.message_user(request, f"Ended {ended_count} auctions and determined winners.")
        else:
            self.message_user(request, "No active auctions found to end.")
    end_auctions.short_description = "End selected active auctions and determine winners"


@admin.register(AuctionBid)
class AuctionBidAdmin(admin.ModelAdmin):
    list_display = ['auction', 'user', 'amount', 'created_at']
    list_filter = ['created_at', 'auction']
    search_fields = ['auction__title', 'user__username']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Bid Information', {
            'fields': ('auction', 'user', 'amount')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(AuctionWinner)
class AuctionWinnerAdmin(admin.ModelAdmin):
    list_display = ['auction', 'winner', 'winning_amount', 'coins_transferred', 'created_at']
    list_filter = ['created_at', 'auction']
    search_fields = ['auction__title', 'winner__username']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Winner Information', {
            'fields': ('auction', 'winner', 'winning_amount', 'coins_transferred')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
