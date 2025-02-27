from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VideoViewSet, CategoryViewSet
from .views.upload_view import UploadView, UploadHistoryView

router = DefaultRouter()
router.register('videos', VideoViewSet)
router.register('categories', CategoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # HTML page routes
    path('upload/', UploadView.as_view(), name='upload'),
    path('upload/history/', UploadHistoryView.as_view(), name='upload_history'),
]
