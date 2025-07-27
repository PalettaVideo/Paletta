"""
API URL patterns for the videos app.
Used exclusively for API endpoints under /api/ prefix.
"""

from django.urls import path
from .views.viewsets import ContentTypeViewSet
from .views.api_views import (
    UnifiedVideoListAPIView, VideoDetailAPIView, PopularTagsAPIView, VideoAPIUploadView,
    S3MultipartUploadView, S3UploadPartView, S3CompleteMultipartUploadView, S3AbortMultipartUploadView
)
from .views.tag_views import TagsAPIView
from .views.video_management_views import TagSuggestionsAPIView
from .views.thumbnail_view import VideoThumbnailAPIView

# API URL patterns (no api/ prefix - will be added by main urls.py)
urlpatterns = [
    # Core API - Video CRUD operations
    path('videos/', UnifiedVideoListAPIView.as_view(), name='api_videos_list'),
    path('videos/<int:video_id>/', VideoDetailAPIView.as_view(), name='api_video_detail'),
    path('uploads/', VideoAPIUploadView.as_view(), name='api_upload'),  # Standardized to plural
    
    # Content Type APIs - Library-specific content type system  
    path('content-types/', ContentTypeViewSet.as_view({'get': 'list'}), name='api_content_types'),
    path('content-type-videos/', UnifiedVideoListAPIView.as_view(), name='api_content_type_videos'),
    
    # S3 Multipart Upload APIs - For large file uploads
    path('s3/create-multipart-upload/', S3MultipartUploadView.as_view(), name='api_s3_create_multipart'),
    path('s3/get-upload-part-url/', S3UploadPartView.as_view(), name='api_s3_upload_part'),
    path('s3/complete-multipart-upload/', S3CompleteMultipartUploadView.as_view(), name='api_s3_complete_multipart'),
    path('s3/abort-multipart-upload/', S3AbortMultipartUploadView.as_view(), name='api_s3_abort_multipart'),
    
    # Media & Metadata APIs - File and thumbnail handling
    path('clip/<int:clip_id>/thumbnail/', VideoThumbnailAPIView.as_view(), name='api_clip_thumbnail'),
    
    # Tag & Search APIs - Tagging and discovery
    path('videos/<int:video_id>/tags/', TagsAPIView.as_view(), name='api_video_tags'),
    path('popular-tags/', PopularTagsAPIView.as_view(), name='api_popular_tags'),
    path('tag-suggestions/', TagSuggestionsAPIView.as_view(), name='api_tag_suggestions'),
] 