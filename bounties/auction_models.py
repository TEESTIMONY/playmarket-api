"""
Auction models for the PlayMarket auction system.

This module contains the database models for auctions, bids, and related functionality.
Designed for high-performance with 1000+ concurrent users.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
import json


class AuctionBid(models.Model):
    """
    Bid model representing individual bids on auctions.
    
    Features:
    - Atomic bid processing with race condition prevention
    - Bid validation and minimum increment enforcement
    - Coin reservation and transfer handling
    - Optimized for high-frequency bid operations
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),      # Bid under review
        ('accepted', 'Accepted'),    # Bid is valid and active
        ('rejected', 'Rejected'),    # Bid was rejected
        ('outbid', 'Outbid'),        # Bid was surpassed by higher bid
        ('cancelled', 'Cancelled'),  # Bid was cancelled
    ]
    
    # Bid information
    auction = models.ForeignKey('bounties.Auction', on_delete=models.CASCADE, related_name='bids')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auction_bids')
    amount = models.IntegerField(help_text="Bid amount in coins")
    
    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Bid validation
    minimum_required = models.IntegerField(help_text="Minimum amount required for this bid")
    previous_highest_bid = models.IntegerField(default=0, help_text="Previous highest bid when this bid was placed")
    
    # Coin handling
    coins_reserved = models.BooleanField(default=False, help_text="Whether coins have been reserved for this bid")
    coins_deducted = models.BooleanField(default=False, help_text="Whether coins have been deducted from user balance")
    
    class Meta:
        ordering = ['-amount', '-created_at']
        indexes = [
            models.Index(fields=['auction', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['amount']),
            models.Index(fields=['created_at']),
            models.Index(fields=['auction', 'amount']),
        ]
        # Ensure user can only have one active bid per auction
        constraints = [
            models.UniqueConstraint(
                fields=['auction', 'user'],
                condition=models.Q(status='accepted'),
                name='unique_active_bid_per_user'
            )
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.auction.title} - {self.amount} coins"
    
    def clean(self):
        """Validate bid before saving."""
        from django.core.exceptions import ValidationError
        
        # Check if auction allows bids
        if not self.auction.is_active:
            raise ValidationError("Auction is not accepting bids")
        
        # Check minimum bid
        if self.amount < self.auction.minimum_bid:
            raise ValidationError(f"Bid must be at least {self.auction.minimum_bid} coins")
        
        # Check minimum increment (typically 1 coin, but can be configured)
        current_highest = self.auction.current_highest_bid
        if self.amount <= current_highest:
            raise ValidationError(f"Bid must be higher than current highest bid ({current_highest} coins)")
    
    def place_bid(self):
        """Place a bid with full validation and atomic processing."""
        with transaction.atomic():
            # Lock the auction row to prevent race conditions
            from .models import Auction
            auction = Auction.objects.select_for_update().get(pk=self.auction.pk)
            
            # Re-validate in case state changed
            if not auction.is_active:
                raise ValueError("Auction is not accepting bids")
            
            # Check user balance
            from .models import UserProfile  # Import here to avoid circular import
            try:
                profile = UserProfile.objects.select_for_update().get(user=self.user)
            except UserProfile.DoesNotExist:
                raise ValueError("User profile not found")
            
            if profile.coin_balance < self.amount:
                raise ValueError("Insufficient coin balance")
            
            # Check minimum increment
            if self.amount <= auction.current_highest_bid:
                raise ValueError(f"Bid must be higher than current highest bid ({auction.current_highest_bid} coins)")
            
            # Reserve coins
            profile.coin_balance -= self.amount
            profile.save(update_fields=['coin_balance'])
            
            # Update previous highest bid status to 'outbid'
            if auction.current_highest_bidder:
                previous_bid = AuctionBid.objects.filter(
                    auction=auction,
                    user=auction.current_highest_bidder,
                    status='accepted'
                ).first()
                if previous_bid:
                    previous_bid.status = 'outbid'
                    previous_bid.save()
            
            # Update auction with new highest bid
            auction.current_highest_bid = self.amount
            auction.current_highest_bidder = self.user
            auction.total_bids += 1
            auction.save()
            
            # Save this bid
            self.status = 'accepted'
            self.coins_reserved = True
            self.coins_deducted = True
            self.previous_highest_bid = auction.current_highest_bid - self.amount
            self.save()
            
            return True
    
    def cancel_bid(self):
        """Cancel bid and refund coins."""
        with transaction.atomic():
            if self.status not in ['pending', 'accepted']:
                raise ValueError("Cannot cancel this bid")
            
            # Refund coins
            from .models import UserProfile
            profile = UserProfile.objects.select_for_update().get(user=self.user)
            profile.coin_balance += self.amount
            profile.save(update_fields=['coin_balance'])
            
            # Update bid status
            self.status = 'cancelled'
            self.coins_reserved = False
            self.coins_deducted = False
            self.save()
            
            # Update auction if this was the highest bid
            if self.auction.current_highest_bidder == self.user:
                # Find new highest bid
                new_highest = self.auction.bids.filter(
                    status='accepted'
                ).exclude(pk=self.pk).order_by('-amount').first()
                
                if new_highest:
                    self.auction.current_highest_bid = new_highest.amount
                    self.auction.current_highest_bidder = new_highest.user
                else:
                    self.auction.current_highest_bid = 0
                    self.auction.current_highest_bidder = None
                
                self.auction.save()


class AuctionWinner(models.Model):
    """
    Model to track auction winners and final settlements.
    
    This provides an audit trail for completed auctions and handles
    the final coin transfer from winner to the system/admin.
    """
    
    auction = models.OneToOneField('bounties.Auction', on_delete=models.CASCADE, related_name='winner')
    winner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auction_wins')
    winning_amount = models.IntegerField(help_text="Final winning bid amount")
    coins_transferred = models.BooleanField(default=False, help_text="Whether coins have been transferred to admin/system")
    transfer_completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['winner']),
            models.Index(fields=['created_at']),
            models.Index(fields=['coins_transferred']),
        ]
    
    def __str__(self):
        return f"{self.winner.username} won {self.auction.title} for {self.winning_amount} coins"
    
    def complete_transfer(self):
        """Complete the coin transfer from winner to system."""
        with transaction.atomic():
            # Lock winner's profile
            from .models import UserProfile
            profile = UserProfile.objects.select_for_update().get(user=self.winner)
            
            # Verify winner still has the coins (they might have spent them)
            if profile.coin_balance < self.winning_amount:
                raise ValueError("Winner no longer has sufficient coins")
            
            # Transfer coins (deduct from winner - admin will handle receiving)
            profile.coin_balance -= self.winning_amount
            profile.save(update_fields=['coin_balance'])
            
            # Mark transfer as completed
            self.coins_transferred = True
            self.transfer_completed_at = timezone.now()
            self.save()
            
            # Create transaction record
            from .models import CoinTransaction
            CoinTransaction.objects.create(
                user=self.winner,
                amount=-self.winning_amount,  # Negative for deduction
                transaction_type='auction_payment',
                reference_id=str(self.auction.id),
                description=f"Payment for winning auction: {self.auction.title}"
            )
            
            return True