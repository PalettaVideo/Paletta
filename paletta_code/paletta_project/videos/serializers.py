from rest_framework import serializers
from .models import Video, ContentType, Tag, VideoTag, PalettaContentType
from .services import AWSCloudStorageService

class ContentTypeSerializer(serializers.ModelSerializer):
    """
    BACKEND/FRONTEND-READY: Serializer for ContentType model (primary classification).
    MAPPED TO: /api/content-types/ endpoint
    USED BY: Content type selection dropdowns, content type listing pages
    
    Provides content type data with video counts for frontend display.
    Includes computed field: display_name, video_count
    """
    video_count = serializers.SerializerMethodField()
    display_name = serializers.ReadOnlyField()
    
    class Meta:
        model = ContentType
        fields = ('id', 'subject_area', 'display_name', 'custom_name', 'library', 'is_active', 'video_count')
        read_only_fields = ('display_name', 'video_count')
    
    def get_video_count(self, obj):
        """Get the count of videos with this content type."""
        return obj.videos.count()



class PalettaContentTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for the PalettaContentType model.
    """
    display_name = serializers.ReadOnlyField()
    
    class Meta:
        model = PalettaContentType
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
    BACKEND/FRONTEND-READY: Comprehensive video serializer with content type structure.
    MAPPED TO: /api/videos/ endpoints
    USED BY: Video listings, detail views, upload forms
    
    Handles video data with content types and streaming URLs.
    Includes validation for title/description lengths.
    """
    uploaded_by_username = serializers.ReadOnlyField(source='uploader.username')
    content_type_name = serializers.ReadOnlyField(source='content_type.display_name')
    library_name = serializers.ReadOnlyField(source='library.name')
    tags = serializers.SerializerMethodField()
    video_file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    storage_status_display = serializers.SerializerMethodField()
    display_content_types = serializers.ReadOnlyField()
    
    class Meta:
        model = Video
        fields = ('id', 'title', 'description', 'content_type', 'content_type_name',
                  'library', 'library_name', 'uploader', 'uploaded_by_username', 'upload_date', 
                  'updated_at', 'tags', 'video_file', 'video_file_url', 'thumbnail', 'thumbnail_url',
                  'duration', 'file_size', 'views_count', 'storage_status', 'storage_status_display', 
                  'storage_url', 'display_content_types')
        read_only_fields = ('uploader', 'upload_date', 'updated_at', 'views_count', 
                           'storage_status', 'storage_url', 'download_link', 'download_link_expiry',
                           'file_size', 'duration', 'display_content_types')
    

    
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
        BACKEND/FRONTEND-READY: Generate video streaming URL for playback.
        MAPPED TO: Video player components
        USED BY: Video detail pages, embedded players
        
        Returns S3 streaming URL for stored videos or local file URL for pending uploads.
        Handles both S3-stored and locally-stored video files.
        Required fields: obj.storage_status, obj.storage_reference_id or obj.video_file
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
        if len(value.split()) > 20:
            raise serializers.ValidationError("Title cannot exceed 20 words.")
        return value
        
    def validate_description(self, value):
        """Validate the description length."""
        if value and len(value.split()) > 100:
            raise serializers.ValidationError("Description cannot exceed 100 words.")
        return value 