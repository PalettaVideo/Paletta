from django.urls import path
from . import views

urlpatterns = [
    # Cart and checkout
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('cart/remove/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    
    # Order management
    path('orders/', views.OrdersListView.as_view(), name='orders_list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
] 