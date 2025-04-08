# Import views from individual files
from .upload_view import UploadView, UploadHistoryView, VideoAPIUploadView, VideoMetadataAPIView
from .viewsets import VideoViewSet, CategoryViewSet
from .download_view import DownloadRequestView
from .clip_store_view import ClipStoreView, CategoryClipView
from .api_views import (
    VideoListAPIView, 
    VideoDetailAPIView, 
    CategoryVideosAPIView, 
    PopularTagsAPIView
)
from .video_detail_view import VideoDetailView
from .tag_views import assign_tags, TagsAPIView

# Export all views to make them available when importing from videos.views
__all__ = [
    'UploadView',
    'UploadHistoryView',
    'VideoViewSet',
    'CategoryViewSet',
    'DownloadRequestView',
    'ClipStoreView',
    'CategoryClipView',
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