from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VideoViewSet, CategoryViewSet
from .views.upload_view import UploadView, UploadHistoryView, VideoAPIUploadView, VideoMetadataAPIView
from .views.download_view import DownloadRequestView
from .views.clip_store_view import ClipStoreView, CategoryClipView
from .views.api_views import VideoListAPIView, VideoDetailAPIView, CategoryVideosAPIView, PopularTagsAPIView

# Create a router for REST API viewsets
router = DefaultRouter()
router.register('videos', VideoViewSet, basename='video')
router.register('categories', CategoryViewSet, basename='category')

# URL patterns for the videos app
urlpatterns = [
    # Frontend views
    path('upload/', UploadView.as_view(), name='upload'),
    path('upload/history/', UploadHistoryView.as_view(), name='upload_history'),
    
    # Clip store views
    path('clips/', ClipStoreView.as_view(), name='clip_store'),
    path('clips/category/<str:category>/', CategoryClipView.as_view(), name='category_clips'),
    
    # API endpoint for categories that matches the frontend expectation
    path('categories/', CategoryViewSet.as_view({'get': 'list'}), name='api_categories'),
    
    # Include the router URLs without the nested path
    path('', include(router.urls)),
    
    # API endpoints for video functionality
    path('api/extract-metadata/', VideoMetadataAPIView.as_view(), name='extract_metadata'),
    path('api/upload/', VideoAPIUploadView.as_view(), name='api_upload'),
    path('download/request/<int:video_id>/', DownloadRequestView.as_view(), name='request_download'),
    
    # Video API endpoints
    path('api/videos/', VideoListAPIView.as_view(), name='api_videos_list'),
    path('api/videos/<int:video_id>/', VideoDetailAPIView.as_view(), name='api_video_detail'),
    path('api/categories/<str:category_name>/videos/', CategoryVideosAPIView.as_view(), name='api_category_videos'),
    path('api/popular-tags/', PopularTagsAPIView.as_view(), name='api_popular_tags'),
]
