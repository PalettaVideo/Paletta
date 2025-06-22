from rest_framework import serializers
from .models import Library, UserLibraryRole
from accounts.serializers import UserSerializer
from videos.serializers import VideoSerializer

class UserLibraryRoleSerializer(serializers.ModelSerializer):
    """
    Serializer for the UserLibraryRole model.
    Includes user details for easier frontend integration.
    """
    user_details = UserSerializer(source='user', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = UserLibraryRole
        fields = ['id', 'user', 'library', 'role', 'added_at', 'user_details', 'role_display']
        read_only_fields = ['added_at']

class LibrarySerializer(serializers.ModelSerializer):
    """
    Serializer for the Library model.
    Includes owner details and related counts for easier frontend integration.
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
        return UserLibraryRole.objects.filter(library=obj).count()
        
    def get_categories_count(self, obj):
        """Get the count of categories in this library."""
        return obj.categories.count()
        
    def get_videos_count(self, obj):
        """Get the count of videos in this library."""
        return obj.videos.count()
        
    def get_logo_url(self, obj):
        """Get the absolute URL for the library logo."""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None
        
    def validate_name(self, value):
        """Validate the length of the library name."""
        if len(value) > 100:
            raise serializers.ValidationError("Library name cannot exceed 100 characters.")
        return value
        
    def validate_color_scheme(self, value):
        """Validate the color scheme JSON structure."""
        required_keys = ['primary', 'secondary', 'text']
        
        # If not provided, don't validate (the model will set defaults)
        if not value:
            return value
            
        # Ensure all required keys are present
        missing_keys = [key for key in required_keys if key not in value]
        if missing_keys:
            raise serializers.ValidationError(f"Missing required keys: {', '.join(missing_keys)}")
            
        # Validate color format (basic check for hex colors)
        for key in required_keys:
            if key in value:
                color = value[key]
                if not color.startswith('#') or len(color) not in [4, 7, 9]:  # #RGB, #RRGGBB, #RRGGBBAA
                    raise serializers.ValidationError(f"Invalid color format for {key}: {color}")
                    
        return value 