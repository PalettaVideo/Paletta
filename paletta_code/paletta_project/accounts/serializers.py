from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password

class UserSerializer(serializers.ModelSerializer):
    # password field is write-only and required
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    # password_confirm field is write-only and required
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
        # validate that the password and password_confirm fields match
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        # create a new user
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        # set the institution, company, and role of the user
        user.institution = validated_data.get('institution', '')
        user.company = validated_data.get('company', '')
        user.role = validated_data.get('role', 'contributor')
        user.save()
        
        return user

    def update(self, instance, validated_data):
        # update the password of the user if provided
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        # update the user with the newly validated password
        return super().update(instance, validated_data) 