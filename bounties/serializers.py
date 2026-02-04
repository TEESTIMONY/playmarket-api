from rest_framework import serializers
from django.utils import timezone
from .models import Bounty, BountyClaim, RedeemCode


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
