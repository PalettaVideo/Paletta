from rest_framework import serializers
from .models import Video, Category, Tag, VideoTag, Upload
from .services import AWSCloudStorageService

class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the Category model with enum-based subject area and content type.
    Includes validation to ensure only predefined combinations are allowed.
    """
    video_count = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    display_name = serializers.ReadOnlyField(source='name')
    slug = serializers.ReadOnlyField()
    subject_area_display = serializers.SerializerMethodField()
    content_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ('id', 'subject_area', 'content_type', 'subject_area_display', 'content_type_display', 
                 'display_name', 'slug', 'description', 'library', 'is_active', 'created_at', 
                 'video_count', 'image', 'image_url')
        read_only_fields = ('created_at', 'video_count', 'display_name', 'slug')
    
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
    
    def get_subject_area_display(self, obj):
        """Get the display name for subject area."""
        return dict(Category.SUBJECT_AREA_CHOICES).get(obj.subject_area, obj.subject_area)
    
    def get_content_type_display(self, obj):
        """Get the display name for content type."""
        return dict(Category.CONTENT_TYPE_CHOICES).get(obj.content_type, obj.content_type)
    
    def validate_subject_area(self, value):
        """Validate that subject area is from the predefined choices."""
        valid_choices = [choice[0] for choice in Category.SUBJECT_AREA_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(
                f"Invalid subject area. Must be one of: {', '.join(valid_choices)}"
            )
        return value
    
    def validate_content_type(self, value):
        """Validate that content type is from the predefined choices."""
        valid_choices = [choice[0] for choice in Category.CONTENT_TYPE_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(
                f"Invalid content type. Must be one of: {', '.join(valid_choices)}"
            )
        return value
    
    def validate(self, data):
        """Validate that the combination of subject_area and content_type is unique per library."""
        library = data.get('library')
        subject_area = data.get('subject_area')
        content_type = data.get('content_type')
        
        if library and subject_area and content_type:
            # Check if this combination already exists for this library (excluding current instance if updating)
            existing_query = Category.objects.filter(
                library=library,
                subject_area=subject_area,
                content_type=content_type
            )
            
            # If updating, exclude the current instance
            if self.instance:
                existing_query = existing_query.exclude(pk=self.instance.pk)
            
            if existing_query.exists():
                raise serializers.ValidationError(
                    "This category combination already exists for this library."
                )
        
        return data

class CategoryListSerializer(serializers.Serializer):
    """
    Serializer for listing all available category combinations without requiring a library.
    Used for displaying options in forms.
    """
    subject_area = serializers.CharField()
    content_type = serializers.CharField()
    display_name = serializers.CharField()
    slug = serializers.CharField()
    subject_area_display = serializers.CharField()
    content_type_display = serializers.CharField()

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
    category_subject_area = serializers.ReadOnlyField(source='category.subject_area')
    category_content_type = serializers.ReadOnlyField(source='category.content_type')
    category_slug = serializers.ReadOnlyField(source='category.slug')
    library_name = serializers.ReadOnlyField(source='library.name')
    tags = serializers.SerializerMethodField()
    video_file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    storage_status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Video
        fields = ('id', 'title', 'description', 'category', 'category_name', 'category_subject_area',
                  'category_content_type', 'category_slug', 'library', 'library_name', 'uploader', 
                  'uploaded_by_username', 'upload_date', 'updated_at', 'tags', 'video_file', 
                  'video_file_url', 'thumbnail', 'thumbnail_url',
                  'duration', 'file_size', 'views_count',
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
        """
        Get the absolute URL for the video file.
        If the video is stored in S3, a temporary streaming URL is generated.
        Otherwise, the local file URL is returned.
        """
        if obj.storage_status == 'stored' and obj.storage_reference_id:
            storage_service = AWSCloudStorageService()
            return storage_service.generate_streaming_url(obj)
            
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