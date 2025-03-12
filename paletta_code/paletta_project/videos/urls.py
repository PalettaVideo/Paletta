from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VideoViewSet, CategoryViewSet
from .views.upload_view import UploadView, UploadHistoryView, VideoAPIUploadView, VideoMetadataAPIView
from .views.download_view import RequestDownloadView

# Create a router for REST API viewsets
router = DefaultRouter()
router.register('videos', VideoViewSet, basename='video')
router.register('categories', CategoryViewSet, basename='category')

# URL patterns for the videos app
urlpatterns = [
    # Frontend views
    path('upload/', UploadView.as_view(), name='upload'),
    path('upload/history/', UploadHistoryView.as_view(), name='upload_history'),
    
    # API endpoint for categories that matches the frontend expectation
    path('categories/', CategoryViewSet.as_view({'get': 'list'}), name='api_categories'),
    
    # Include the router URLs without the nested path
    path('', include(router.urls)),
    
    # API endpoints for other functionality
    path('api/extract-metadata/', VideoMetadataAPIView.as_view(), name='extract_metadata'),
    path('api/upload/', VideoAPIUploadView.as_view(), name='api_upload'),
    path('download/request/<int:video_id>/', RequestDownloadView.as_view(), name='request_download'),
]
