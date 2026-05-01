from rest_framework import serializers
from users.models import Club, ClubAdmin


class ClubAdminMiniSerializer(serializers.ModelSerializer):
    """Minimal ClubAdmin representation for the transfer request dropdown."""
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model  = ClubAdmin
        fields = ['id', 'username', 'position']


class ClubSerializer(serializers.ModelSerializer):
    """Used in list views and nested inside event/notification serializers."""
    class Meta:
        model  = Club
        fields = ['id', 'name', 'description', 'slug']
        read_only_fields = ['id']


class ClubDetailSerializer(serializers.ModelSerializer):
    """
    Used only on GET /api/clubs/<slug>/ — includes the admins list so
    the My Club dashboard can populate the transfer request dropdown
    without needing a separate endpoint.
    """
    admins = ClubAdminMiniSerializer(many=True, read_only=True)

    class Meta:
        model  = Club
        fields = ['id', 'name', 'description', 'slug', 'admins']
        read_only_fields = ['id']
