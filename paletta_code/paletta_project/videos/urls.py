"""
BACKEND/FRONTEND-READY: URL routing configuration for videos app.
MAPPED TO: /videos/ base path 
USED BY: Django URL dispatcher, frontend AJAX calls, admin interface

Organizes video-related endpoints: upload, management, API, content types, downloads.
Groups related functionality for better maintainability.
"""

from django.urls import path
from .views.upload_view import MyVideosView
from .views.download_view import DownloadRequestView
from .views.tag_views import assign_tags
from .views.video_management_views import VideoEditView, VideoDeleteView
from .views.page_views import UploadPageView

# URL patterns for the videos app (frontend only)
urlpatterns = [
    # Frontend Pages - User-facing HTML pages
    path('upload/', UploadPageView.as_view(), name='upload'),
    path('my-videos/', MyVideosView.as_view(), name='my_videos'),
    path('edit/<int:video_id>/', VideoEditView.as_view(), name='edit_video'),
    path('delete/<int:video_id>/', VideoDeleteView.as_view(), name='delete_video'),
    path('download/request/<int:video_id>/', DownloadRequestView.as_view(), name='request_download'),
    
    # Tag Management - Video tagging operations
    path('videos/<int:video_id>/tags/', assign_tags, name='assign_tags'),
]
