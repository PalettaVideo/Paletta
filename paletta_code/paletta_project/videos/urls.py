from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VideoViewSet, CategoryViewSet
from .views.upload_view import UploadView, UploadHistoryView, VideoAPIUploadView
from .views.download_view import RequestDownloadView

# Create a router for REST API viewsets
router = DefaultRouter()
router.register('videos', VideoViewSet, basename='video')
router.register('categories', CategoryViewSet, basename='category')

# URL patterns for the videos app
urlpatterns = [
    # REST API endpoints
    path('api/', include(router.urls)),
    path('api/upload/', VideoAPIUploadView.as_view(), name='api_upload'),
    
    # Web UI endpoints
    path('upload/', UploadView.as_view(), name='upload'),
    path('upload/history/', UploadHistoryView.as_view(), name='upload_history'),
    path('download/request/<int:video_id>/', RequestDownloadView.as_view(), name='request_download'),
]
