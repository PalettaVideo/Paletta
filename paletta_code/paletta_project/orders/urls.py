"""
FRONTEND-READY: URL routing configuration for orders app frontend pages.
MAPPED TO: /orders/ base path for HTML pages only
USED BY: Django URL dispatcher for order management frontend

Organizes order-related frontend pages: cart, checkout, order history.
API endpoints are now in api_urls.py for clean separation.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Frontend Pages - User-facing HTML pages for orders
    path('cart/', views.CartView.as_view(), name='cart'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('orders/', views.OrdersListView.as_view(), name='orders_list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
] 