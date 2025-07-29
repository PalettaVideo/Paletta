from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password

class UserSerializer(serializers.ModelSerializer):
    """
    BACKEND/FRONTEND-READY: Comprehensive user serializer for API operations.
    MAPPED TO: /api/users/ endpoints
    USED BY: User registration, profile management, and authentication
    
    Handles user data serialization with password validation and confirmation.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'password', 'password_confirm', 
                  'institution', 'company', 'role', 'created_at')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'created_at': {'read_only': True}
        }

    def validate(self, attrs):
        """
        BACKEND-READY: Validate password confirmation matches.
        MAPPED TO: User registration and update validation
        USED BY: User creation and profile update endpoints
        
        Ensures password and password_confirm fields match before processing.
        """
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        """
        BACKEND-READY: Create new user with validated data.
        MAPPED TO: POST /api/users/
        USED BY: User registration endpoint
        
        Creates user account with proper password hashing and default role.
        Required fields: email, password, first_name, last_name
        """
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.institution = validated_data.get('institution', '')
        user.company = validated_data.get('company', '')
        user.role = validated_data.get('role', 'user')
        user.save()
        
        return user

    def update(self, instance, validated_data):
        """
        BACKEND-READY: Update existing user with validated data.
        MAPPED TO: PUT/PATCH /api/users/{id}/
        USED BY: Profile update endpoints
        
        Updates user fields with proper password handling and rehashing.
        """
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        return super().update(instance, validated_data) 