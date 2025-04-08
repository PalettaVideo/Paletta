from rest_framework import serializers
from .models import Video, Category, Tag, VideoTag, Upload

class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the Category model.
    Includes the image URL for easy access in the frontend.
    """
    video_count = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'description', 'library', 'created_at', 'video_count', 'image', 'image_url')
        read_only_fields = ('created_at', 'video_count')
    
    def get_video_count(self, obj):
        """Get the count of videos in this category."""
        return obj.videos.count()
    
    def get_image_url(self, obj):
        """Get the absolute URL for the category image."""
        if hasattr(obj, 'image') and obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for the Tag model.
    """
    videos_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = ('id', 'name', 'library', 'videos_count')
        
    def get_videos_count(self, obj):
        """Get the count of videos with this tag."""
        # We need to count through the VideoTag model now
        return VideoTag.objects.filter(tag=obj).count()

class VideoSerializer(serializers.ModelSerializer):
    """
    Serializer for the Video model.
    Includes additional fields for easier frontend integration.
    """
    uploaded_by_username = serializers.ReadOnlyField(source='uploader.username')
    category_name = serializers.ReadOnlyField(source='category.name')
    library_name = serializers.ReadOnlyField(source='library.name')
    tags = serializers.SerializerMethodField()
    video_file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    storage_status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Video
        fields = ('id', 'title', 'description', 'category', 'category_name',
                  'library', 'library_name', 'uploader', 'uploaded_by_username', 
                  'upload_date', 'updated_at', 'tags', 'video_file', 
                  'video_file_url', 'thumbnail', 'thumbnail_url',
                  'duration', 'file_size', 'views_count', 'is_published',
                  'storage_status', 'storage_status_display', 'storage_url')
        read_only_fields = ('uploader', 'upload_date', 'updated_at', 'views_count', 
                           'storage_status', 'storage_url', 'download_link', 'download_link_expiry',
                           'file_size', 'duration')
    
    def get_tags(self, obj):
        """Get all tags for this video through VideoTag."""
        video_tags = VideoTag.objects.filter(video=obj).select_related('tag')
        return TagSerializer(
            [vt.tag for vt in video_tags], 
            many=True, 
            context=self.context
        ).data
    
    def get_video_file_url(self, obj):
        """Get the absolute URL for the video file."""
        if obj.video_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.video_file.url)
            return obj.video_file.url
        return None
    
    def get_thumbnail_url(self, obj):
        """Get the absolute URL for the thumbnail."""
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None
    
    def get_storage_status_display(self, obj):
        """Get the display value for the storage status."""
        return dict(Video.STORAGE_STATUS_CHOICES).get(obj.storage_status, obj.storage_status)
        
    def validate_title(self, value):
        """Validate the title length."""
        if len(value.split()) > 25:
            raise serializers.ValidationError("Title cannot exceed 25 words.")
        return value
        
    def validate_description(self, value):
        """Validate the description length."""
        if value and len(value.split()) > 100:
            raise serializers.ValidationError("Description cannot exceed 100 words.")
        return value 