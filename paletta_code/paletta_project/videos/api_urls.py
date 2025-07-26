"""
API URL patterns for the videos app.
Used exclusively for API endpoints under /api/ prefix.
"""

from django.urls import path
from .views.viewsets import ContentTypeViewSet
from .views.api_views import UnifiedVideoListAPIView, VideoDetailAPIView, PopularTagsAPIView, VideoAPIUploadView
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
    
    # Media & Metadata APIs - File and thumbnail handling
    path('clip/<int:clip_id>/thumbnail/', VideoThumbnailAPIView.as_view(), name='api_clip_thumbnail'),
    
    # Tag & Search APIs - Tagging and discovery
    path('videos/<int:video_id>/tags/', TagsAPIView.as_view(), name='api_video_tags'),
    path('popular-tags/', PopularTagsAPIView.as_view(), name='api_popular_tags'),
    path('tag-suggestions/', TagSuggestionsAPIView.as_view(), name='api_tag_suggestions'),
] 