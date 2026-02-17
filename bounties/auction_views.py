"""
Auction API views for the PlayMarket auction system.

This module contains Django REST Framework views for managing auctions,
bidding, and real-time auction updates.
"""

import os

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, Max
from django.contrib.auth.decorators import login_required
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
import django.db.models as models
from datetime import timedelta

from .models import UserProfile
from .models import Auction, AuctionImage
from .auction_models import AuctionBid, AuctionWinner
from .serializers import AuctionSerializer, AuctionBidSerializer, AuctionWinnerSerializer
from .authentication import FirebaseAuthentication

logger = logging.getLogger(__name__)


def _get_admin_identity_allowlist():
    """Load admin identity allowlist from environment variables."""
    admin_emails_env = os.environ.get('ADMIN_EMAILS', '')
    admin_emails = {
        email.strip().lower()
        for email in admin_emails_env.split(',')
        if email.strip()
    }

    superuser_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '').strip().lower()
    if superuser_email:
        admin_emails.add(superuser_email)

    return admin_emails


def _has_admin_privileges(user):
    """Return True if user should be treated as an admin."""
    if not user or not getattr(user, 'is_authenticated', False):
        return False

    if user.is_superuser or user.is_staff:
        return True

    admin_allowlist = _get_admin_identity_allowlist()
    identity_candidates = {
        (getattr(user, 'email', '') or '').strip().lower(),
        (getattr(user, 'username', '') or '').strip().lower(),
    }
    if admin_allowlist and any(identity in admin_allowlist for identity in identity_candidates if identity):
        return True

    try:
        return bool(user.profile.is_admin)
    except UserProfile.DoesNotExist:
        return False


class AuctionListView(ListAPIView):
    """
    List all active auctions.
    Admins can see all auctions, regular users only see active ones.
    """
    serializer_class = AuctionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        now = timezone.now()

        if _has_admin_privileges(user):
            # Admins see all auctions
            return Auction.objects.all().prefetch_related('images').order_by('-created_at')
        else:
            # Regular users see only active auctions
            return Auction.objects.filter(
                Q(status='active') | Q(status='upcoming'),
                starts_at__lte=now
            ).prefetch_related('images').order_by('ends_at')


class AuctionDetailView(RetrieveAPIView):
    """
    Get detailed information about a specific auction.
    """
    queryset = Auction.objects.all().prefetch_related('images')
    serializer_class = AuctionSerializer
    permission_classes = [permissions.IsAuthenticated]


class CreateAuctionView(APIView):
    """
    Create a new auction (Admin only).
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [FirebaseAuthentication]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def post(self, request):
        user = request.user

        # Check if user is admin
        if not _has_admin_privileges(user):
            profile_is_admin = False
            try:
                profile_is_admin = bool(user.profile.is_admin)
            except UserProfile.DoesNotExist:
                profile_is_admin = False

            admin_allowlist = _get_admin_identity_allowlist()
            email_value = (getattr(user, 'email', '') or '').strip().lower()
            username_value = (getattr(user, 'username', '') or '').strip().lower()

            logger.warning(
                "Auction create denied for user=%s email=%s is_superuser=%s is_staff=%s profile_is_admin=%s allowlist_email_match=%s allowlist_username_match=%s",
                user.username,
                getattr(user, 'email', ''),
                user.is_superuser,
                user.is_staff,
                profile_is_admin,
                email_value in admin_allowlist if admin_allowlist else False,
                username_value in admin_allowlist if admin_allowlist else False,
            )
            return Response(
                {'error': 'Admin privileges required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if there's already an active auction
        active_auction = Auction.objects.filter(status='active').first()
        if active_auction:
            return Response(
                {
                    'error': 'Cannot create new auction while another auction is active',
                    'active_auction': {
                        'id': active_auction.id,
                        'title': active_auction.title,
                        'ends_at': active_auction.ends_at
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = AuctionSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    auction = serializer.save(created_by=user)

                    now = timezone.now()
                    if auction.starts_at <= now < auction.ends_at:
                        auction.status = 'active'
                    elif now < auction.starts_at:
                        auction.status = 'upcoming'
                    else:
                        auction.status = 'ended'
                    auction.save(update_fields=['status'])

                    uploaded_images = request.FILES.getlist('images') or request.FILES.getlist('image_files')
                    stored_image_urls = []

                    for index, image_file in enumerate(uploaded_images):
                        auction_image = AuctionImage.objects.create(
                            auction=auction,
                            image=image_file,
                            order=index
                        )
                        if auction_image.image:
                            # Store relative media path so URLs remain valid across
                            # environments/domains (localhost, Render, custom domains).
                            stored_image_urls.append(auction_image.image.url)

                    if stored_image_urls:
                        auction.image_urls = stored_image_urls
                        auction.save(update_fields=['image_urls'])
                    
                    # Broadcast auction creation to all connected clients
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        'auction_updates',
                        {
                            'type': 'auction_broadcast',
                            'data': {
                                'type': 'auction_created',
                                'auction': AuctionSerializer(auction, context={'request': request}).data,
                                'timestamp': timezone.now().isoformat()
                            }
                        }
                    )
                    
                    logger.info(f"Auction created by admin {user.username}: {auction.title}")
                    
                    return Response(
                        AuctionSerializer(auction, context={'request': request}).data,
                        status=status.HTTP_201_CREATED
                    )
                    
            except Exception as e:
                logger.error(f"Error creating auction: {str(e)}")
                return Response(
                    {'error': 'Failed to create auction'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAuctionView(APIView):
    """
    Delete an auction (Admin only).
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [FirebaseAuthentication]

    def delete(self, request, auction_id):
        user = request.user

        # Check if user is admin
        if not _has_admin_privileges(user):
            return Response(
                {'error': 'Admin privileges required'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            auction = Auction.objects.get(id=auction_id)
            auction_title = auction.title
            deleted_auction_id = auction.id
            auction.delete()

            # Broadcast auction deletion to connected clients
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'auction_updates',
                {
                    'type': 'auction_broadcast',
                    'data': {
                        'type': 'auction_deleted',
                        'auction_id': deleted_auction_id,
                        'title': auction_title,
                        'timestamp': timezone.now().isoformat()
                    }
                }
            )

            logger.info(f"Auction deleted by admin {user.username}: {auction_title} (ID: {deleted_auction_id})")

            return Response(
                {'message': 'Auction deleted successfully'},
                status=status.HTTP_200_OK
            )

        except Auction.DoesNotExist:
            return Response(
                {'error': 'Auction not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class PlaceBidView(APIView):
    """
    Place a bid on an auction.
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [FirebaseAuthentication]
    
    def post(self, request, auction_id):
        user = request.user
        
        try:
            with transaction.atomic():
                # Get user profile (locked for safe balance updates)
                user_profile = UserProfile.objects.select_for_update().get(user=user)

                # Get auction (locked to prevent race conditions on highest bid updates)
                auction = Auction.objects.select_for_update().get(id=auction_id)
                now = timezone.now()

                # Auto-sync auction status with actual time window
                if auction.status == 'upcoming' and auction.starts_at <= now < auction.ends_at:
                    auction.status = 'active'
                    auction.save(update_fields=['status'])
                elif auction.status == 'active' and auction.ends_at <= now:
                    auction.status = 'ended'
                    auction.save(update_fields=['status'])

                # Validate auction status
                if auction.status != 'active':
                    return Response(
                        {
                            'error': 'Auction is not active',
                            'status': auction.status,
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Validate auction start time
                if auction.starts_at > now:
                    return Response(
                        {'error': 'Auction has not started yet'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Validate auction end time
                if auction.ends_at <= now:
                    return Response(
                        {'error': 'Auction has ended'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Get bid amount from request
                bid_amount = request.data.get('amount')
                try:
                    bid_amount = int(bid_amount)
                except (TypeError, ValueError):
                    bid_amount = 0

                if bid_amount <= 0:
                    return Response(
                        {'error': 'Invalid bid amount'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Validate user has enough coins
                if user_profile.coin_balance < bid_amount:
                    return Response(
                        {'error': 'Insufficient coins'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Validate minimum bid
                current_highest_bid = auction.current_highest_bid
                min_bid = current_highest_bid + 1 if current_highest_bid else auction.minimum_bid

                if bid_amount < min_bid:
                    return Response(
                        {'error': f'Bid must be at least {min_bid} coins'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Mark previous accepted bid(s) as outbid before creating a new accepted bid
                AuctionBid.objects.filter(
                    auction=auction,
                    user=user,
                    status='accepted'
                ).update(status='outbid')

                if auction.current_highest_bidder and auction.current_highest_bidder != user:
                    AuctionBid.objects.filter(
                        auction=auction,
                        user=auction.current_highest_bidder,
                        status='accepted'
                    ).update(status='outbid')

                # Create bid record with required auction bid fields
                bid = AuctionBid.objects.create(
                    auction=auction,
                    user=user,
                    amount=bid_amount,
                    status='accepted',
                    minimum_required=int(min_bid),
                    previous_highest_bid=int(current_highest_bid or 0),
                    coins_reserved=True,
                    coins_deducted=True,
                )

                # Deduct coins from user
                user_profile.coin_balance -= bid_amount
                user_profile.save(update_fields=['coin_balance'])

                # Update auction state
                extension_applied = False
                extension_message = None
                extension_threshold_seconds = 3 * 60
                extension_delta = timedelta(minutes=3)

                # Anti-snipe: extend auction by 3 minutes only when bid is placed
                # at exactly 3 minutes remaining (second-level precision).
                remaining_seconds = round((auction.ends_at - now).total_seconds())
                if remaining_seconds == extension_threshold_seconds:
                    auction.ends_at = auction.ends_at + extension_delta
                    extension_applied = True
                    extension_message = 'A new highest bid placed 3 mins before the end will extend the auction by 3 min'

                auction.current_highest_bid = bid_amount
                auction.current_highest_bidder = user
                auction.total_bids += 1
                auction_update_fields = ['current_highest_bid', 'current_highest_bidder', 'total_bids']
                if extension_applied:
                    auction_update_fields.append('ends_at')
                auction.save(update_fields=auction_update_fields)

                # Broadcast bid update to auction group
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'auction_{auction.id}',
                    {
                        'type': 'auction_update',
                        'data': {
                            'type': 'new_bid',
                            'auction_id': auction.id,
                            'user': user.username,
                            'amount': bid_amount,
                            'timestamp': timezone.now().isoformat(),
                            'current_highest_bid': bid_amount,
                            'bid_count': auction.total_bids,
                            'auction_extended': extension_applied,
                            'extension_minutes': 3 if extension_applied else 0,
                            'new_end_time': auction.ends_at.isoformat() if extension_applied else None,
                            'extension_message': extension_message,
                        }
                    }
                )

                # Broadcast to leaderboard group
                async_to_sync(channel_layer.group_send)(
                    f'leaderboard_{auction.id}',
                    {
                        'type': 'leaderboard_update',
                        'data': {
                            'type': 'bid_update',
                            'auction_id': auction.id,
                            'current_highest_bid': bid_amount,
                            'highest_bidder': user.username,
                            'bid_count': auction.total_bids,
                            'auction_extended': extension_applied,
                            'extension_minutes': 3 if extension_applied else 0,
                            'new_end_time': auction.ends_at.isoformat() if extension_applied else None,
                        }
                    }
                )

                logger.info(f"Bid placed by {user.username} on auction {auction.title}: {bid_amount} coins")

                return Response(
                    {
                        'message': 'Bid placed successfully',
                        'bid': AuctionBidSerializer(bid).data,
                        'remaining_coins': user_profile.coin_balance,
                        'extension_applied': extension_applied,
                        'extension_minutes': 3 if extension_applied else 0,
                        'new_ends_at': auction.ends_at.isoformat() if extension_applied else None,
                        'extension_message': extension_message,
                    },
                    status=status.HTTP_201_CREATED
                )
                
        except Auction.DoesNotExist:
            return Response(
                {'error': 'Auction not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception(f"Error placing bid: {str(e)}")
            return Response(
                {'error': 'Failed to place bid'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AuctionStatusView(APIView):
    """
    Update auction status (Admin only).
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [FirebaseAuthentication]
    
    def patch(self, request, auction_id):
        user = request.user

        # Check if user is admin
        if not _has_admin_privileges(user):
            return Response(
                {'error': 'Admin privileges required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            auction = Auction.objects.get(id=auction_id)
            
            new_status = request.data.get('status')
            valid_statuses = ['active', 'upcoming', 'ended', 'cancelled']
            
            if new_status not in valid_statuses:
                return Response(
                    {'error': f'Invalid status. Valid options: {", ".join(valid_statuses)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            old_status = auction.status
            auction.status = new_status
            auction.save()
            
            # Broadcast status change
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'auction_{auction.id}',
                {
                    'type': 'auction_update',
                    'data': {
                        'type': 'status_changed',
                        'auction_id': auction.id,
                        'old_status': old_status,
                        'new_status': new_status,
                        'timestamp': timezone.now().isoformat()
                    }
                }
            )
            
            logger.info(f"Auction status changed by admin {user.username}: {auction.title} {old_status} -> {new_status}")
            
            return Response(
                {'message': 'Auction status updated', 'status': new_status},
                status=status.HTTP_200_OK
            )
            
        except Auction.DoesNotExist:
            return Response(
                {'error': 'Auction not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class EndAuctionView(APIView):
    """
    Manually end an auction and determine winner (Admin only).
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [FirebaseAuthentication]
    
    def post(self, request, auction_id):
        user = request.user

        # Check if user is admin
        if not _has_admin_privileges(user):
            return Response(
                {'error': 'Admin privileges required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            with transaction.atomic():
                auction = Auction.objects.select_for_update().get(id=auction_id)
                
                if auction.status != 'active':
                    return Response(
                        {'error': 'Auction is not active'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Get highest bid
                highest_bid = AuctionBid.objects.filter(
                    auction=auction,
                    status='accepted'
                ).order_by('-amount').first()
                if not highest_bid:
                    return Response(
                        {'error': 'No bids found for this auction'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Create winner record
                winner = AuctionWinner.objects.create(
                    auction=auction,
                    winner=highest_bid.user,
                    winning_amount=highest_bid.amount,
                    coins_transferred=False,
                )
                
                # Update auction status
                auction.status = 'ended'
                auction.save()
                
                # Broadcast auction end and winner
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'auction_{auction.id}',
                    {
                        'type': 'auction_update',
                        'data': {
                            'type': 'auction_ended',
                            'auction_id': auction.id,
                            'winner': {
                                'username': winner.winner.username,
                                'winning_bid': winner.winning_amount
                            },
                            'timestamp': timezone.now().isoformat()
                        }
                    }
                )
                
                logger.info(f"Auction ended by admin {user.username}: {auction.title}, winner: {winner.winner.username}")
                
                return Response(
                    {
                        'message': 'Auction ended successfully',
                        'winner': AuctionWinnerSerializer(winner).data
                    },
                    status=status.HTTP_200_OK
                )
                
        except Auction.DoesNotExist:
            return Response(
                {'error': 'Auction not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error ending auction: {str(e)}")
            return Response(
                {'error': 'Failed to end auction'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AuctionLeaderboardView(APIView):
    """
    Get auction leaderboard with top bidders.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, auction_id):
        try:
            auction = Auction.objects.get(id=auction_id)
            
            # Get top 10 bidders by highest bid amount
            top_bidders = AuctionBid.objects.filter(
                auction=auction
            ).values('user__username').annotate(
                total_bids=models.Count('id'),
                highest_bid=models.Max('amount')
            ).order_by('-highest_bid')[:10]
            
            # Get current highest bid
            current_highest_bid = auction.current_highest_bid
            current_highest_bidder = None
            
            if current_highest_bid:
                latest_bid = AuctionBid.objects.filter(
                    auction=auction,
                    amount=current_highest_bid
                ).first()
                if latest_bid:
                    current_highest_bidder = latest_bid.user.username
            
            return Response({
                'auction_id': auction_id,
                'current_highest_bid': current_highest_bid,
                'current_highest_bidder': current_highest_bidder,
                'total_bids': auction.total_bids,
                'top_bidders': list(top_bidders)
            })
            
        except Auction.DoesNotExist:
            return Response(
                {'error': 'Auction not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class UserAuctionHistoryView(APIView):
    """
    Get user's auction participation history.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get user's bids
        user_bids = AuctionBid.objects.filter(user=user).select_related('auction')
        
        # Get user's wins
        user_wins = AuctionWinner.objects.filter(winner=user).select_related('auction')
        
        return Response({
            'bids': AuctionBidSerializer(user_bids, many=True).data,
            'wins': AuctionWinnerSerializer(user_wins, many=True).data,
            'total_bids': user_bids.count(),
            'total_wins': user_wins.count()
        })


# Utility function to check auction timers and end auctions
def check_auction_timers():
    """
    Utility function to check and end auctions that have expired.
    This should be called periodically (e.g., via Celery beat).
    """
    now = timezone.now()
    
    # Find auctions that should be ended
    expiring_auctions = Auction.objects.filter(
        status='active',
        ends_at__lte=now
    )
    
    for auction in expiring_auctions:
        try:
            with transaction.atomic():
                # Get highest bid
                highest_bid = AuctionBid.objects.filter(
                    auction=auction,
                    status='accepted'
                ).order_by('-amount').first()
                
                if highest_bid:
                    # Create winner record
                    winner = AuctionWinner.objects.create(
                        auction=auction,
                        winner=highest_bid.user,
                        winning_amount=highest_bid.amount,
                        coins_transferred=False,
                    )
                
                # Update auction status
                auction.status = 'ended'
                auction.save()
                
                # Broadcast auction end
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'auction_{auction.id}',
                    {
                        'type': 'auction_update',
                        'data': {
                            'type': 'auction_ended',
                            'auction_id': auction.id,
                            'winner': {
                                'username': winner.winner.username if highest_bid else None,
                                'winning_bid': winner.winning_amount if highest_bid else None
                            },
                            'timestamp': now.isoformat()
                        }
                    }
                )
                
                logger.info(f"Auction expired and ended: {auction.title}")
                
        except Exception as e:
            logger.error(f"Error ending expired auction {auction.id}: {str(e)}")