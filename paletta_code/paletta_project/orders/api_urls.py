"""
BACKEND-READY: API URL patterns for the orders app.
Used exclusively for API endpoints under /api/orders/ prefix.
"""

from django.urls import path
from . import views

# API URL patterns (no api/ prefix - will be added by main urls.py as /api/orders/)
urlpatterns = [
    # Cart Management - AJAX endpoints for cart operations
    path('add-to-cart/', views.AddToCartView.as_view(), name='api_add_to_cart'),
    path('remove-from-cart/', views.RemoveFromCartView.as_view(), name='api_remove_from_cart'),
    
    # Collection Management - User collection operations  
    path('add-to-collection/', views.AddToCollectionView.as_view(), name='api_add_to_collection'),
    path('remove-from-collection/', views.RemoveFromCollectionView.as_view(), name='api_remove_from_collection'),
    
    # Download Request APIs - Video download system
    path('request-download/', views.DownloadRequestAPIView.as_view(), name='api_request_download'),
    path('download-requests/', views.DownloadRequestStatusAPIView.as_view(), name='api_download_requests_status'),
    path('download-requests/<int:request_id>/resend/', views.ResendDownloadEmailAPIView.as_view(), name='api_resend_download_email'),
    path('bulk-download-request/', views.bulk_download_request, name='api_bulk_download_request'),
] 