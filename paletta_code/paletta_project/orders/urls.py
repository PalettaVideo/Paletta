"""
BACKEND/FRONTEND-READY: URL routing configuration for orders app.
MAPPED TO: /orders/ base path for HTML pages, /api/ for API endpoints
USED BY: Django URL dispatcher, frontend AJAX calls, cart/checkout flows

Organizes order-related endpoints: cart management, checkout, order history, download requests.
Follows same pattern as videos app with mixed HTML pages and API endpoints.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Frontend Pages - User-facing HTML pages for orders
    path('cart/', views.CartView.as_view(), name='cart'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('orders/', views.OrdersListView.as_view(), name='orders_list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    
    # Cart Management - AJAX endpoints for cart operations
    path('add-to-cart/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('remove-from-cart/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    
    # Collection Management - User collection operations  
    path('add-to-collection/', views.AddToCollectionView.as_view(), name='add_to_collection'),
    path('remove-from-collection/', views.RemoveFromCollectionView.as_view(), name='remove_from_collection'),
    
    # Download Request APIs - Video download system
    path('request-download/', views.DownloadRequestAPIView.as_view(), name='api_request_download'),
    path('download-requests/', views.DownloadRequestStatusAPIView.as_view(), name='api_download_requests_status'),
    path('download-requests/<int:request_id>/resend/', views.ResendDownloadEmailAPIView.as_view(), name='api_resend_download_email'),
    path('bulk-download-request/', views.bulk_download_request, name='api_bulk_download_request'),
] 