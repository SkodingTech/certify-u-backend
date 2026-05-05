from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
from users.models.user import *
from django.contrib.auth.models import User

excludeData = ['updated_at', 'is_deleted']

##### Users Serializers #####
class UserLoginSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='user_profile.role', read_only=True)
    image = serializers.ImageField(source='user_profile.image', read_only=True)
    banner = serializers.ImageField(source='user_profile.banner', read_only=True)
    is_instructor = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email', 'first_name', 'last_name', 'role', 'is_instructor', 'image', 'banner')
        extra_kwargs = {'password': {'write_only': True}}
    
    def get_is_instructor(self, obj):
        return hasattr(obj, 'instructorprofile')

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
   
class UserProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)

    class Meta:
        model = UserProfile
        exclude = excludeData

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user
        
        # Update User fields
        if 'first_name' in user_data:
            user.first_name = user_data.get('first_name')
        if 'last_name' in user_data:
            user.last_name = user_data.get('last_name')
        user.save()

        # Update Profile fields
        return super().update(instance, validated_data)
        
class StudentsProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        exclude = excludeData
        
class InstructorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructorProfile
        exclude = excludeData