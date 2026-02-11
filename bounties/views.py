from rest_framework import generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction, models
from .models import Bounty, BountyClaim, RedeemCode, UserProfile, CoinTransaction
from .serializers import (
    BountySerializer, BountyDetailSerializer,
    BountyClaimSerializer, BountyClaimCreateSerializer,
    BountySubmissionSerializer,
    RedeemCodeSerializer, RedeemCodeCreateSerializer, RedeemCodeRedeemSerializer
)


class BountyListView(generics.ListCreateAPIView):
    queryset = Bounty.objects.all()
    serializer_class = BountySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Optimized query with annotations for better performance
        queryset = Bounty.objects.annotate(
            claims_count=models.Count('claims'),
            active_claims_count=models.Count('claims', filter=models.Q(claims__status__in=['pending', 'submitted']))
        ).select_related()

        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Order by created_at before slicing
        queryset = queryset.order_by('-created_at')

        # Remove artificial limit to show all bounties
        # limit = self.request.query_params.get('limit', 50)  # Default to 50 bounties
        # try:
        #     limit = min(int(limit), 100)  # Max 100 bounties
        #     queryset = queryset[:limit]
        # except (ValueError, TypeError):
        #     pass

        return queryset

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return super().get_permissions()


class BountyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Bounty.objects.all()
    serializer_class = BountyDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()


class BountyClaimView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, bounty_id):
        bounty = get_object_or_404(Bounty, id=bounty_id)

        # Check if user already claimed this bounty
        existing_claim = BountyClaim.objects.filter(
            bounty=bounty,
            user=request.user
        ).first()

        if existing_claim:
            return Response(
                {"error": "You have already claimed this bounty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if bounty is available
        if bounty.status != 'available' or bounty.claims_left <= 0:
            return Response(
                {"error": "Bounty is not available for claiming"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create claim and update bounty
        with transaction.atomic():
            claim = BountyClaim.objects.create(bounty=bounty, user=request.user)
            # Force update the bounty status and claims_left by calling save() without update_fields
            bounty.save()  # This will trigger the save method logic

        serializer = BountyClaimSerializer(claim)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BountySubmitView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, bounty_id):
        claim = get_object_or_404(
            BountyClaim,
            bounty_id=bounty_id,
            user=request.user,
            status='pending'
        )

        serializer = BountySubmissionSerializer(claim, data=request.data, partial=True)
        if serializer.is_valid():
            claim.status = 'submitted'
            claim.submitted_at = timezone.now()
            claim.submission = serializer.validated_data['submission']
            claim.save()
            return Response(BountyClaimSerializer(claim).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserBountyClaimsView(generics.ListAPIView):
    serializer_class = BountyClaimSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BountyClaim.objects.filter(user=self.request.user).select_related('bounty', 'user')


class BountyClaimApprovalView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, claim_id):
        claim = get_object_or_404(
            BountyClaim,
            id=claim_id,
            status='submitted'  # Only allow approving submitted claims
        )

        with transaction.atomic():
            claim.status = 'approved'
            claim.approved_at = timezone.now()
            claim.save()

            # Add coins to user's balance
            profile, created = UserProfile.objects.get_or_create(user=claim.user)
            new_balance = profile.add_coins(
                claim.bounty.reward,
                'bounty_reward',
                claim.id,
                f"Bounty reward for '{claim.bounty.title}'"
            )

        serializer = BountyClaimSerializer(claim)
        data = serializer.data
        data['new_balance'] = new_balance
        return Response(data)


class RedeemCodeListView(generics.ListCreateAPIView):
    queryset = RedeemCode.objects.all()
    serializer_class = RedeemCodeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RedeemCodeCreateSerializer
        return RedeemCodeSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = RedeemCode.objects.select_related('used_by')
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset


class RedeemCodeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = RedeemCode.objects.all()
    serializer_class = RedeemCodeSerializer
    permission_classes = [permissions.IsAdminUser]


class RedeemCodeRedeemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        import json
        try:
            # Parse JSON from request body directly to avoid RawPostDataException
            data = json.loads(request.body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = RedeemCodeRedeemSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        code = serializer.validated_data['code'].upper()  # Make case insensitive
        redeem_code = get_object_or_404(RedeemCode, code=code)

        # Check if code is valid
        if not redeem_code.is_valid():
            if redeem_code.status == 'used':
                return Response(
                    {"error": "This redeem code has already been used"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif redeem_code.status == 'expired':
                return Response(
                    {"error": "This redeem code has expired"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {"error": "This redeem code is not valid"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Check if user already used this code
        if RedeemCode.objects.filter(code=code, used_by=request.user).exists():
            return Response(
                {"error": "You have already used this redeem code"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Redeem the code
        with transaction.atomic():
            redeem_code.status = 'used'
            redeem_code.used_by = request.user
            redeem_code.used_at = timezone.now()
            redeem_code.save()

            # Add coins to user's balance
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            new_balance = profile.add_coins(
                redeem_code.coins,
                'code_redemption',
                redeem_code.id,
                f"Redeemed code '{redeem_code.code}'"
            )

        return Response({
            "message": f"Successfully redeemed {redeem_code.coins} coins!",
            "coins": redeem_code.coins,
            "new_balance": new_balance
        })


class UserBalanceView(APIView):
    """
    Get user's current coin balance
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        return Response({
            'balance': profile.coin_balance,
            'user': request.user.username
        })


class UserTransactionsView(generics.ListAPIView):
    """
    Get user's transaction history
    """
    serializer_class = None  # We'll create a simple response
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CoinTransaction.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        transactions = self.get_queryset()
        data = []
        for transaction in transactions:
            data.append({
                'id': transaction.id,
                'amount': transaction.amount,
                'transaction_type': transaction.transaction_type,
                'description': transaction.description,
                'reference_id': transaction.reference_id,
                'created_at': transaction.created_at
            })

        return Response({
            'transactions': data,
            'count': len(data)
        })


class AdminUserBalanceAdjustmentView(APIView):
    """
    Admin endpoint to adjust user balances
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        user_id = request.data.get('user_id')
        amount = request.data.get('amount')
        reason = request.data.get('reason', 'Admin adjustment')

        if not user_id or amount is None:
            return Response(
                {'error': 'user_id and amount are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            amount = int(amount)
        except ValueError:
            return Response(
                {'error': 'amount must be a valid integer'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        profile, created = UserProfile.objects.get_or_create(user=user)
        new_balance = profile.add_coins(amount, 'admin_adjustment', 0, reason)

        return Response({
            'user': user.username,
            'old_balance': profile.coin_balance - amount,
            'new_balance': new_balance,
            'adjustment': amount,
            'reason': reason
        })


class UserDetailView(APIView):
    """
    Get comprehensive user information including profile, balance, transactions, etc.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=user)

        # Get recent transactions (last 10)
        recent_transactions = CoinTransaction.objects.filter(user=user)[:10]

        # Get bounty claims
        bounty_claims = BountyClaim.objects.filter(user=user).select_related('bounty')

        # Get redeem codes used
        used_codes = RedeemCode.objects.filter(used_by=user).select_related()

        # Calculate stats
        total_bounties_completed = bounty_claims.filter(status='approved').count()
        total_coins_earned = sum(
            transaction.amount for transaction in CoinTransaction.objects.filter(
                user=user, amount__gt=0
            )
        )
        total_codes_redeemed = used_codes.count()

        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_joined': user.date_joined,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'profile': {
                'coin_balance': profile.coin_balance,
                'profile_created': not created,
            },
            'stats': {
                'total_bounties_completed': total_bounties_completed,
                'total_coins_earned': total_coins_earned,
                'total_codes_redeemed': total_codes_redeemed,
                'current_balance': profile.coin_balance,
            },
            'recent_transactions': [
                {
                    'id': tx.id,
                    'amount': tx.amount,
                    'transaction_type': tx.transaction_type,
                    'description': tx.description,
                    'reference_id': tx.reference_id,
                    'created_at': tx.created_at,
                } for tx in recent_transactions
            ],
            'bounty_claims': [
                {
                    'id': claim.id,
                    'bounty_title': claim.bounty.title,
                    'bounty_reward': claim.bounty.reward,
                    'status': claim.status,
                    'submitted_at': claim.submitted_at,
                    'approved_at': claim.approved_at,
                    'created_at': claim.created_at,
                } for claim in bounty_claims
            ],
            'used_codes': [
                {
                    'id': code.id,
                    'code': code.code,
                    'coins': code.coins,
                    'used_at': code.used_at,
                    'created_at': code.created_at,
                } for code in used_codes
            ],
        }

        return Response(user_data)


class UserListView(generics.ListAPIView):
    """
    Admin view to get all users with their profiles
    """
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return User.objects.all().select_related('profile')

    def list(self, request, *args, **kwargs):
        users = self.get_queryset()
        data = []
        for user in users:
            profile = getattr(user, 'profile', None)
            data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'date_joined': user.date_joined,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'is_active': user.is_active,
                'coin_balance': profile.coin_balance if profile else 0,
                'last_login': user.last_login,
            })

        return Response({
            'users': data,
            'count': len(data)
        })
