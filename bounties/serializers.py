from rest_framework import serializers
from django.utils import timezone
from urllib.parse import urlparse
from .models import Bounty, BountyClaim, RedeemCode, Auction, AuctionImage
from .auction_models import AuctionBid, AuctionWinner


class BountySerializer(serializers.ModelSerializer):
    time_left = serializers.SerializerMethodField()
    posted_hours_ago = serializers.SerializerMethodField()

    class Meta:
        model = Bounty
        fields = [
            'id', 'title', 'description', 'reward', 'status',
            'claims_left', 'max_claims', 'expires_at', 'created_at', 'time_left', 'posted_hours_ago'
        ]

    def get_time_left(self, obj):
        if obj.expires_at:
            remaining = obj.expires_at - timezone.now()
            if remaining.total_seconds() > 0:
                hours = int(remaining.total_seconds() // 3600)
                return hours
        return None

    def get_posted_hours_ago(self, obj):
        elapsed = timezone.now() - obj.created_at
        return int(elapsed.total_seconds() // 3600)


class BountyDetailSerializer(BountySerializer):
    claims_count = serializers.SerializerMethodField()

    class Meta(BountySerializer.Meta):
        fields = BountySerializer.Meta.fields + ['claims_count', 'max_claims']

    def get_claims_count(self, obj):
        return obj.claims.count()


class BountyClaimSerializer(serializers.ModelSerializer):
    bounty_title = serializers.CharField(source='bounty.title', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = BountyClaim
        fields = [
            'id', 'bounty', 'bounty_title', 'user', 'user_username',
            'status', 'submission', 'submitted_at', 'approved_at', 'created_at'
        ]
        read_only_fields = ['bounty_title', 'user_username', 'submitted_at', 'approved_at']


class BountyClaimCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BountyClaim
        fields = ['bounty', 'user']
        extra_kwargs = {
            'user': {'read_only': True}
        }

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class BountySubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BountyClaim
        fields = ['submission']


class RedeemCodeSerializer(serializers.ModelSerializer):
    used_by_username = serializers.CharField(source='used_by.username', read_only=True)
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = RedeemCode
        fields = [
            'id', 'code', 'coins', 'status', 'expires_at',
            'used_by', 'used_by_username', 'used_at', 'created_at',
            'is_valid'
        ]
        read_only_fields = ['used_by_username', 'used_at', 'is_valid']

    def get_is_valid(self, obj):
        return obj.is_valid()


class RedeemCodeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RedeemCode
        fields = ['code', 'coins', 'expires_at']


class RedeemCodeRedeemSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)


# Auction System Serializers
class AuctionImageSerializer(serializers.ModelSerializer):
    """Serializer for AuctionImage model."""
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = AuctionImage
        fields = ['id', 'image', 'order', 'created_at']
        read_only_fields = ['created_at']

    def get_image(self, obj):
        request = self.context.get('request')
        if not obj.image:
            return None

        image_url = obj.image.url
        return request.build_absolute_uri(image_url) if request else image_url


class AuctionSerializer(serializers.ModelSerializer):
    """Serializer for Auction model."""
    current_highest_bid = serializers.SerializerMethodField()
    bid_count = serializers.SerializerMethodField()
    time_until_start = serializers.SerializerMethodField()
    time_until_end = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    image_files = AuctionImageSerializer(source='images', many=True, read_only=True)

    class Meta:
        model = Auction
        fields = [
            'id', 'title', 'description', 'minimum_bid', 'status',
            'starts_at', 'ends_at', 'created_at', 'updated_at', 'created_by',
            'current_highest_bid', 'bid_count', 'time_until_start', 
            'time_until_end', 'is_active', 'images', 'image_files'
        ]
        read_only_fields = ['status', 'created_at', 'created_by', 'current_highest_bid', 'bid_count', 'image_files']

    def get_current_highest_bid(self, obj):
        return obj.current_highest_bid

    def get_bid_count(self, obj):
        return obj.total_bids

    def get_time_until_start(self, obj):
        if obj.starts_at:
            remaining = obj.starts_at - timezone.now()
            if remaining.total_seconds() > 0:
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                return f"{hours}h {minutes}m"
        return None

    def get_time_until_end(self, obj):
        if obj.ends_at:
            remaining = obj.ends_at - timezone.now()
            if remaining.total_seconds() > 0:
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                return f"{hours}h {minutes}m"
        return None

    def get_is_active(self, obj):
        return obj.status == 'active'

    def get_images(self, obj):
        """Return auction image URLs for frontend compatibility."""
        request = self.context.get('request')

        def normalize_legacy_url(url):
            """Normalize legacy URLs so host/protocol mismatches do not break images."""
            if not isinstance(url, str):
                return url

            if not request:
                return url

            def normalize_media_path(path):
                if path.startswith('/media/'):
                    return path
                if path.startswith('/auction_images/'):
                    return f"/media{path}"
                return path

            if url.startswith('/'):
                return request.build_absolute_uri(normalize_media_path(url))

            # If an absolute URL points to a stale host (e.g. localhost/old render
            # host) but still references /media/, rebuild with current API host.
            if url.startswith('http://') or url.startswith('https://'):
                parsed = urlparse(url)
                normalized_path = normalize_media_path(parsed.path)
                if normalized_path.startswith('/media/'):
                    normalized = request.build_absolute_uri(normalized_path)
                    if parsed.query:
                        normalized = f"{normalized}?{parsed.query}"
                    return normalized

            return url

        uploaded_images = []
        for image_obj in obj.images.all().order_by('order', 'created_at'):
            if image_obj.image:
                image_url = image_obj.image.url
                uploaded_images.append(
                    request.build_absolute_uri(image_url) if request else image_url
                )

        if uploaded_images:
            return uploaded_images

        legacy_urls = obj.image_urls or []
        if not request:
            return legacy_urls

        normalized_urls = []
        for url in legacy_urls:
            normalized_urls.append(normalize_legacy_url(url))
        return normalized_urls


class AuctionBidSerializer(serializers.ModelSerializer):
    """Serializer for AuctionBid model."""
    username = serializers.CharField(source='user.username', read_only=True)
    auction_title = serializers.CharField(source='auction.title', read_only=True)

    class Meta:
        model = AuctionBid
        fields = [
            'id', 'auction', 'auction_title', 'user', 'username',
            'amount', 'created_at'
        ]
        read_only_fields = ['user', 'username', 'created_at']


class AuctionWinnerSerializer(serializers.ModelSerializer):
    """Serializer for AuctionWinner model."""
    user = serializers.IntegerField(source='winner.id', read_only=True)
    username = serializers.CharField(source='winner.username', read_only=True)
    auction_title = serializers.CharField(source='auction.title', read_only=True)
    winning_bid = serializers.IntegerField(source='winning_amount', read_only=True)
    coins_deducted = serializers.IntegerField(source='winning_amount', read_only=True)
    won_at = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = AuctionWinner
        fields = [
            'id', 'auction', 'auction_title', 'user', 'username',
            'winning_bid', 'coins_deducted', 'won_at',
            'winning_amount', 'coins_transferred', 'transfer_completed_at', 'created_at'
        ]
        read_only_fields = [
            'user', 'username', 'winning_bid', 'coins_deducted', 'won_at',
            'winning_amount', 'coins_transferred', 'transfer_completed_at', 'created_at'
        ]
