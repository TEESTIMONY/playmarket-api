from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """
    User profile with coin balance
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    coin_balance = models.IntegerField(default=0, help_text="User's coin balance")
    is_admin = models.BooleanField(default=False, help_text="Whether user has admin privileges")

    class Meta:
        ordering = ['-user__date_joined']

    def add_coins(self, amount, transaction_type, reference_id, description=""):
        """
        Add coins to user's balance atomically
        """
        from django.db import transaction

        with transaction.atomic():
            # Lock the profile row to prevent race conditions
            profile = UserProfile.objects.select_for_update().get(pk=self.pk)

            # Update balance
            profile.coin_balance += amount
            profile.save(update_fields=['coin_balance'])

            # Create transaction record
            CoinTransaction.objects.create(
                user=self.user,
                amount=amount,
                transaction_type=transaction_type,
                reference_id=str(reference_id),
                description=description
            )

            return profile.coin_balance

    def __str__(self):
        return f"{self.user.username} ({self.coin_balance} coins)"


class CoinTransaction(models.Model):
    """
    Transaction history for coin balance changes
    """
    TRANSACTION_TYPES = [
        ('bounty_reward', 'Bounty Reward'),
        ('code_redemption', 'Code Redemption'),
        ('admin_adjustment', 'Admin Adjustment'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coin_transactions')
    amount = models.IntegerField(help_text="Coin amount (positive for credits, negative for debits)")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255, blank=True)
    reference_id = models.CharField(max_length=100, help_text="ID of related object (bounty claim, redeem code, etc.)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['reference_id']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.amount} coins ({self.transaction_type})"


class Bounty(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('full', 'Full'),
        ('expired', 'Expired'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    reward = models.IntegerField(help_text="Coin reward amount")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    max_claims = models.IntegerField()
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_expired(self):
        return self.expires_at and timezone.now() > self.expires_at

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if not is_new:
            if self.is_expired():
                if self.status != 'expired':
                    self.status = 'expired'
                    super().save(*args, **kwargs)
            elif self.claims_left <= 0:
                if self.status != 'full':
                    self.status = 'full'
                    super().save(*args, **kwargs)

    @property
    def claims_left(self):
        return self.max_claims - self.claims.count()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return self.title


class BountyClaim(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    bounty = models.ForeignKey(Bounty, on_delete=models.CASCADE, related_name='claims')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bounty_claims')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submission = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['bounty', 'user']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['submitted_at']),
            models.Index(fields=['approved_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['bounty', 'status']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.bounty.title}"


class RedeemCode(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('used', 'Used'),
        ('expired', 'Expired'),
    ]

    code = models.CharField(max_length=50, unique=True, help_text="Unique redeem code")
    coins = models.IntegerField(help_text="Number of coins this code gives")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When the code expires")
    used_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='used_codes')
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_expired(self):
        return self.expires_at and timezone.now() > self.expires_at

    def is_valid(self):
        return self.status == 'active' and not self.is_expired()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['status', 'expires_at']),
        ]

    def __str__(self):
        return f"{self.code} - {self.coins} coins"


class Auction(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image_urls = models.JSONField(default=list, blank=True)
    minimum_bid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_auctions')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    current_highest_bid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_highest_bidder = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='highest_bid_auctions')
    total_bids = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'bounties_auctions'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['starts_at']),
            models.Index(fields=['ends_at']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title

    def get_highest_bid(self):
        highest_bid = self.bids.order_by('-amount').first()
        return highest_bid.amount if highest_bid else 0

    def get_highest_bidder(self):
        highest_bid = self.bids.order_by('-amount').first()
        return highest_bid.user if highest_bid else None

    def get_bid_count(self):
        return self.bids.count()

    def get_time_until_start(self):
        now = timezone.now()
        if self.starts_at > now:
            return self.starts_at - now
        return None

    def get_time_until_end(self):
        now = timezone.now()
        if self.ends_at > now:
            return self.ends_at - now
        return None

    def is_active(self):
        now = timezone.now()
        return self.status == 'active' and self.starts_at <= now <= self.ends_at


class AuctionImage(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='auction_images/')
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        db_table = 'bounties_auction_images'

    def __str__(self):
        return f"{self.auction.title} - Image {self.order}"
