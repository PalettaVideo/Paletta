# Import views from individual files
from .main_views import home, about, features, contact
from .upload_view import UploadView, UploadHistoryView, VideoMetadataAPIView
from .download_view import DownloadRequestView
from .clip_store_view import ClipStoreView
from .video_detail_view import VideoDetailView
from .viewsets import VideoViewSet, CategoryViewSet
from .api_views import VideoAPIUploadView
from .api_views import (
    VideoListAPIView, 
    VideoDetailAPIView, 
    CategoryVideosAPIView, 
    PopularTagsAPIView
)
from .tag_views import assign_tags, TagsAPIView

# Export all views to make them available when importing from videos.views
__all__ = [
    'UploadView',
    'UploadHistoryView',
    'VideoViewSet',
    'CategoryViewSet',
    'DownloadRequestView',
    'ClipStoreView',
    'VideoListAPIView',
    'VideoDetailAPIView',
    'CategoryVideosAPIView',
    'PopularTagsAPIView',
    'VideoMetadataAPIView',
    'VideoAPIUploadView',
    'VideoDetailView',
    'assign_tags',
    'TagsAPIView'
] 