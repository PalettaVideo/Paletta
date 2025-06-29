"""
BACKEND/FRONTEND-READY: URL routing configuration for videos app.
MAPPED TO: /videos/ base path 
USED BY: Django URL dispatcher, frontend AJAX calls, admin interface

Organizes video-related endpoints: upload, management, API, categories, downloads.
Groups related functionality for better maintainability.
"""

from django.urls import path
from .views.viewsets import UnifiedCategoryViewSet, ContentTypeViewSet
from .views.upload_view import UploadHistoryView
from .views.download_view import DownloadRequestView
from .views.api_views import VideoListAPIView, VideoDetailAPIView, CategoryVideosAPIView, PopularTagsAPIView, VideoAPIUploadView, ContentTypeVideosAPIView
from .views.tag_views import assign_tags, TagsAPIView
from .views.video_management_views import VideoEditView, VideoDeleteView, TagSuggestionsAPIView
from .views.thumbnail_view import VideoThumbnailAPIView
from .views.page_views import UploadPageView

# URL patterns for the videos app
urlpatterns = [
    # Frontend Pages - User-facing HTML pages
    path('upload/', UploadPageView.as_view(), name='upload'),
    path('upload-history/', UploadHistoryView.as_view(), name='upload_history'),
    path('edit/<int:video_id>/', VideoEditView.as_view(), name='edit_video'),
    path('delete/<int:video_id>/', VideoDeleteView.as_view(), name='delete_video'),
    path('download/request/<int:video_id>/', DownloadRequestView.as_view(), name='request_download'),
    
    # Tag Management - Video tagging operations
    path('videos/<int:video_id>/tags/', assign_tags, name='assign_tags'),
    
    # Core API - Video CRUD operations
    path('api/videos/', VideoListAPIView.as_view(), name='api_videos_list'),
    path('api/videos/<int:video_id>/', VideoDetailAPIView.as_view(), name='api_video_detail'),
    path('api/upload/', VideoAPIUploadView.as_view(), name='api_upload'),
    
    # Category & Content Type APIs - Classification systems
    path('api/categories/', UnifiedCategoryViewSet.as_view(), name='api_unified_categories'),
    path('api/categories/<str:category_name>/videos/', CategoryVideosAPIView.as_view(), name='api_category_videos'),
    path('api/content-types/', ContentTypeViewSet.as_view(), name='api_content_types'),
    path('api/content-type-videos/', ContentTypeVideosAPIView.as_view(), name='api_content_type_videos'),
    
    # Media & Metadata APIs - File and thumbnail handling
    path('api/clip/<int:clip_id>/thumbnail/', VideoThumbnailAPIView.as_view(), name='api_clip_thumbnail'),
    
    # Tag & Search APIs - Tagging and discovery
    path('api/videos/<int:video_id>/tags/', TagsAPIView.as_view(), name='api_video_tags'),
    path('api/popular-tags/', PopularTagsAPIView.as_view(), name='api_popular_tags'),
    path('api/tag-suggestions/', TagSuggestionsAPIView.as_view(), name='api_tag_suggestions'),
]
