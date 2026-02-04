from rest_framework import generics, permissions, pagination
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count
from .models import BountyClaim
from .serializers import BountyClaimSerializer


class BountyClaimsPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to view it,
    or admins to view any object.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to the owner of the object or admin users
        return obj.user == request.user or request.user.is_staff


class UserClaimedBountiesView(generics.ListAPIView):
    """
    API endpoint that returns claimed bounties for a specific user.
    """
    serializer_class = BountyClaimSerializer
    pagination_class = BountyClaimsPagination
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        
        # Allow 'me' as a special case for current user
        if user_id == 'me':
            user = self.request.user
        else:
            user = get_object_or_404(User, id=user_id)
        
        # Check permissions: users can only access their own data unless they're admin
        if user != self.request.user and not self.request.user.is_staff:
            return BountyClaim.objects.none()
        
        return BountyClaim.objects.filter(user=user).select_related('bounty').order_by('-approved_at', '-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Get the user for statistics
        user_id = self.kwargs['user_id']
        if user_id == 'me':
            user = request.user
        else:
            user = get_object_or_404(User, id=user_id)
        
        # Get statistics
        total_claims = queryset.count()
        approved_count = queryset.filter(status='approved').count()
        submitted_count = queryset.filter(status='submitted').count()
        pending_count = queryset.filter(status='pending').count()
        rejected_count = queryset.filter(status='rejected').count()
        
        total_approved_rewards = sum(claim.bounty.reward for claim in queryset if claim.status == 'approved')
        total_pending_rewards = sum(claim.bounty.reward for claim in queryset if claim.status == 'submitted')
        
        # Paginate the results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        # If not paginated, serialize all results
        serializer = self.get_serializer(queryset, many=True)
        
        # Create response with pagination metadata and statistics
        response_data = {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'pagination': {
                'page': 1,
                'page_size': len(serializer.data),
                'total_pages': 1,
                'total_count': total_claims,
                'has_next': False,
                'has_previous': False
            },
            'claimed_bounties': serializer.data,
            'statistics': {
                'total_claims': total_claims,
                'approved': approved_count,
                'submitted': submitted_count,
                'pending': pending_count,
                'rejected': rejected_count,
                'total_approved_rewards': total_approved_rewards,
                'total_pending_rewards': total_pending_rewards
            }
        }
        
        return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_claimed_bounties_stats(request, user_id):
    """
    API endpoint that returns only statistics for a user's claimed bounties.
    """
    # Allow 'me' as a special case for current user
    if user_id == 'me':
        user = request.user
    else:
        user = get_object_or_404(User, id=user_id)
    
    # Check permissions: users can only access their own data unless they're admin
    if user != request.user and not request.user.is_staff:
        return Response({'error': 'Permission denied'}, status=403)
    
    # Get statistics
    queryset = BountyClaim.objects.filter(user=user)
    
    total_claims = queryset.count()
    approved_count = queryset.filter(status='approved').count()
    submitted_count = queryset.filter(status='submitted').count()
    pending_count = queryset.filter(status='pending').count()
    rejected_count = queryset.filter(status='rejected').count()
    
    total_approved_rewards = sum(claim.bounty.reward for claim in queryset if claim.status == 'approved')
    total_pending_rewards = sum(claim.bounty.reward for claim in queryset if claim.status == 'submitted')
    
    response_data = {
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        },
        'statistics': {
            'total_claims': total_claims,
            'approved': approved_count,
            'submitted': submitted_count,
            'pending': pending_count,
            'rejected': rejected_count,
            'total_approved_rewards': total_approved_rewards,
            'total_pending_rewards': total_pending_rewards
        }
    }
    
    return Response(response_data)