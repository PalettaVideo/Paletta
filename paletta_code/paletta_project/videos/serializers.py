from rest_framework import serializers
from .models import Video, Category, Tag, VideoTag, ContentType, PalettaCategory
from .services import AWSCloudStorageService

class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the Category model (subject areas only in new structure).
    """
    video_count = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    display_name = serializers.ReadOnlyField()
    slug = serializers.ReadOnlyField()
    
    class Meta:
        model = Category
        fields = ('id', 'subject_area', 'display_name', 'slug', 'description', 'library', 
                 'is_active', 'created_at', 'video_count', 'image', 'image_url')
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

class ContentTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for the ContentType model.
    """
    display_name = serializers.ReadOnlyField()
    
    class Meta:
        model = ContentType
        fields = ('id', 'code', 'display_name', 'is_active')
        read_only_fields = ('display_name',)

class PalettaCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the PalettaCategory model.
    """
    display_name = serializers.ReadOnlyField()
    
    class Meta:
        model = PalettaCategory
        fields = ('id', 'code', 'display_name', 'description', 'is_active')
        read_only_fields = ('display_name',)

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
        return VideoTag.objects.filter(tag=obj).count()

class VideoSerializer(serializers.ModelSerializer):
    """
    Serializer for the Video model with dual-category structure.
    """
    uploaded_by_username = serializers.ReadOnlyField(source='uploader.username')
    subject_area_name = serializers.ReadOnlyField(source='subject_area.display_name')
    content_type_names = serializers.SerializerMethodField()
    paletta_category_name = serializers.ReadOnlyField(source='paletta_category.display_name')
    library_name = serializers.ReadOnlyField(source='library.name')
    tags = serializers.SerializerMethodField()
    video_file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    storage_status_display = serializers.SerializerMethodField()
    display_categories = serializers.ReadOnlyField()
    
    class Meta:
        model = Video
        fields = ('id', 'title', 'description', 'subject_area', 'subject_area_name', 
                  'content_types', 'content_type_names', 'paletta_category', 'paletta_category_name',
                  'library', 'library_name', 'uploader', 'uploaded_by_username', 'upload_date', 
                  'updated_at', 'tags', 'video_file', 'video_file_url', 'thumbnail', 'thumbnail_url',
                  'duration', 'file_size', 'views_count', 'storage_status', 'storage_status_display', 
                  'storage_url', 'display_categories')
        read_only_fields = ('uploader', 'upload_date', 'updated_at', 'views_count', 
                           'storage_status', 'storage_url', 'download_link', 'download_link_expiry',
                           'file_size', 'duration', 'display_categories')
    
    def get_content_type_names(self, obj):
        """Get display names for all content types."""
        return [ct.display_name for ct in obj.content_types.all()]
    
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