from rest_framework import serializers
from .models import Library, UserLibraryRole
from accounts.serializers import UserSerializer
from videos.serializers import VideoSerializer

class UserLibraryRoleSerializer(serializers.ModelSerializer):
    """
    BACKEND/FRONTEND-READY: Serializer for user library role management.
    MAPPED TO: /api/roles/ endpoints
    USED BY: Role management API views and frontend forms
    
    Handles serialization of user roles within libraries with user details.
    """
    user_details = UserSerializer(source='user', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = UserLibraryRole
        fields = ['id', 'user', 'library', 'role', 'added_at', 'user_details', 'role_display']
        read_only_fields = ['added_at']

class LibrarySerializer(serializers.ModelSerializer):
    """
    BACKEND/FRONTEND-READY: Comprehensive library serializer for API operations.
    MAPPED TO: /api/libraries/ endpoints
    USED BY: Library management views, admin interface, and frontend
    
    Provides full library data with related counts and formatted fields.
    """
    owner_details = UserSerializer(source='owner', read_only=True)
    user_roles = UserLibraryRoleSerializer(many=True, read_only=True)
    categories_count = serializers.SerializerMethodField()
    videos_count = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    color_scheme = serializers.JSONField(required=False)
    storage_limit_display = serializers.CharField(source='get_storage_display', read_only=True)
    storage_limit_gb = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Library
        fields = [
            'id', 'name', 'description', 'logo', 'owner', 'owner_details', 
            'storage_tier', 'storage_limit_display', 'storage_limit_gb',
            'is_active', 'created_at', 'updated_at', 'category_source',
            'member_count', 'color_scheme', 'user_roles', 'categories_count', 'videos_count', 'logo_url'
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at', 'storage_limit_display', 'storage_limit_gb']
        
    def get_member_count(self, obj):
        """
        BACKEND-READY: Count total members in library.
        MAPPED TO: API response field
        USED BY: Library listing and detail views
        
        Returns total count of users with roles in this library.
        """
        return UserLibraryRole.objects.filter(library=obj).count()
        
    def get_categories_count(self, obj):
        """
        BACKEND-READY: Count categories in library.
        MAPPED TO: API response field
        USED BY: Library dashboard and statistics
        
        Returns total count of active categories in this library.
        """
        return obj.categories.count()
        
    def get_videos_count(self, obj):
        """
        BACKEND-READY: Count videos in library.
        MAPPED TO: API response field
        USED BY: Library dashboard and statistics
        
        Returns total count of videos in this library.
        """
        return obj.videos.count()
        
    def get_logo_url(self, obj):
        """
        BACKEND/FRONTEND-READY: Get absolute URL for library logo.
        MAPPED TO: API response field
        USED BY: Frontend components and templates
        
        Returns absolute URL for logo image or None if no logo exists.
        """
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None
        
    def validate_name(self, value):
        """
        BACKEND-READY: Validate library name length.
        MAPPED TO: API validation process
        USED BY: Library creation and update endpoints
        
        Ensures library name doesn't exceed maximum length.
        """
        if len(value) > 100:
            raise serializers.ValidationError("Library name cannot exceed 100 characters.")
        return value
        
    def validate_description(self, value):
        """
        BACKEND-READY: Validate library description word count.
        MAPPED TO: API validation process
        USED BY: Library creation and update endpoints
        
        Ensures description is between 10-200 words for adequate context.
        """
        if value:
            word_count = len(value.strip().split())
            if word_count < 10:
                raise serializers.ValidationError("Description should be at least 10 words to provide adequate context.")
            if word_count > 200:
                raise serializers.ValidationError("Description cannot exceed 200 words. Please shorten your description.")
        return value
        
    def validate_color_scheme(self, value):
        """
        BACKEND-READY: Validate color scheme JSON structure.
        MAPPED TO: API validation process  
        USED BY: Library creation and update endpoints
        
        Validates required color keys and hex format for color schemes.
        """
        required_keys = ['primary', 'secondary', 'text']
        
        if not value:
            return value
            
        missing_keys = [key for key in required_keys if key not in value]
        if missing_keys:
            raise serializers.ValidationError(f"Missing required keys: {', '.join(missing_keys)}")
            
        for key in required_keys:
            if key in value:
                color = value[key]
                if not color.startswith('#') or len(color) not in [4, 7, 9]:  # #RGB, #RRGGBB, #RRGGBBAA
                    raise serializers.ValidationError(f"Invalid color format for {key}: {color}")
                    
        return value 