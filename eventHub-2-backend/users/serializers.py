from django.contrib.auth import get_user_model
from rest_framework import serializers
from users.models import Club, ClubAdmin, ClubAdminTransferRequest, Student
 
User = get_user_model()
 
 
#Club
class ClubSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Club
        fields = ['id', 'name', 'description', 'slug']
        read_only_fields = ['id']
 
 
#ClubAdmin
class ClubAdminSerializer(serializers.ModelSerializer):
    club = ClubSerializer(read_only=True)
 
    class Meta:
        model  = ClubAdmin
        fields = ['id', 'club', 'position']
 
 
#Student
class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Student
        fields = ['major', 'year_group']
 
 
#User Register
class RegisterSerializer(serializers.ModelSerializer):
    password   = serializers.CharField(write_only=True, min_length=8)
    major      = serializers.CharField(write_only=True, required=False)
    year_group = serializers.IntegerField(write_only=True, required=False)
 
    class Meta:
        model  = User
        fields = ['id', 'email', 'username', 'password', 'role', 'major', 'year_group']
        read_only_fields = ['id']
        extra_kwargs = {'role': {'default': User.Role.STUDENT}}
 
    def validate_role(self, value):
        """
        Public registration is for students only.
        Club admins and system admins are assigned by the system admin
        through the Django admin panel or the assign-club-admin endpoint.
        Reject any attempt to register with a privileged role directly.
        """
        if value != User.Role.STUDENT:
            raise serializers.ValidationError(
                'Only student accounts can be created through registration. '
                'Club admin roles are assigned by the system admin.'
            )
        return value
 
    def create(self, validated_data):
        major      = validated_data.pop('major', None)
        year_group = validated_data.pop('year_group', None)
        user       = User.objects.create_user(**validated_data)
        if user.role == User.Role.STUDENT and major and year_group:
            Student.objects.create(user=user, major=major, year_group=year_group)
        return user
 
 
#User
class UserSerializer(serializers.ModelSerializer):
    club_profile    = serializers.SerializerMethodField()
    student_profile = serializers.SerializerMethodField()
 
    class Meta:
        model  = User
        fields = ['id', 'email', 'username', 'role', 'club_profile', 'student_profile']
        read_only_fields = ['id', 'role']
 
    def get_club_profile(self, obj):
        if obj.role == User.Role.CLUB_ADMIN:
            try:
                return ClubAdminSerializer(obj.club_admin_profile).data
            except ClubAdmin.DoesNotExist:
                return None
        return None
 
    def get_student_profile(self, obj):
        if obj.role == User.Role.STUDENT:
            try:
                return StudentSerializer(obj.student).data
            except Student.DoesNotExist:
                return None
        return None
 
 

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'email', 'username', 'role']
        read_only_fields = ['id', 'email', 'username', 'role']
 
 
#Transfer Request
class TransferRequestSerializer(serializers.ModelSerializer):
    requester        = UserListSerializer(read_only=True)
    admin_to_replace = ClubAdminSerializer(read_only=True)
    club             = ClubSerializer(read_only=True)
 
    club_id             = serializers.UUIDField(write_only=True)
    admin_to_replace_id = serializers.IntegerField(write_only=True)
    reason              = serializers.CharField()
 
    class Meta:
        model  = ClubAdminTransferRequest
        fields = [
            'id', 'club', 'club_id',
            'requester',
            'admin_to_replace', 'admin_to_replace_id',
            'reason', 'status',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'requester', 'status', 'created_at', 'updated_at']
 
    def validate(self, data):
        try:
            admin = ClubAdmin.objects.get(
                pk=data['admin_to_replace_id'],
                club_id=data['club_id'],
            )
        except ClubAdmin.DoesNotExist:
            raise serializers.ValidationError(
                'The selected admin does not belong to this club.'
            )
        data['admin_to_replace'] = admin
        return data
 
    def create(self, validated_data):
        validated_data['requester'] = self.context['request'].user
        validated_data.pop('admin_to_replace_id', None)
        return super().create(validated_data)