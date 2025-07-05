from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
import json

from .models import Order, OrderDetail
from videos.models import Video
from libraries.models import Library

class CartView(LoginRequiredMixin, ListView):
    """View for displaying the current user's shopping cart."""
    template_name = 'orders/cart.html'
    context_object_name = 'cart_items'
    
    def get_queryset(self):
        """Return the user's current cart as a list of videos."""
        # Get or create an order with 'pending' status for the current user
        library_id = self.request.session.get('current_library_id')
        
        if not library_id:
            # Default to Paletta library if none is set
            try:
                library = Library.objects.get(name='Paletta')
                library_id = library.id
            except Library.DoesNotExist:
                return OrderDetail.objects.none()
        
        order, created = Order.objects.get_or_create(
            user=self.request.user, 
            payment_status='pending',
            library_id=library_id,
            defaults={'order_date': timezone.now()}
        )
        
        return OrderDetail.objects.filter(order=order).select_related('video')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate total price
        cart_items = context['cart_items']
        total_price = sum(item.price for item in cart_items)
        context['total_price'] = total_price
        
        # Get the current library
        library_id = self.request.session.get('current_library_id')
        if library_id:
            try:
                context['current_library'] = Library.objects.get(id=library_id)
            except Library.DoesNotExist:
                pass
        
        return context

class OrdersListView(LoginRequiredMixin, ListView):
    """View for displaying a user's order history."""
    template_name = 'orders/orders_list.html'
    context_object_name = 'orders'
    
    def get_queryset(self):
        """Return all completed orders for the current user."""
        return Order.objects.filter(
            user=self.request.user,
            payment_status='completed'
        ).order_by('-order_date')

    def get_context_data(self, **kwargs):
        """Add library context to the orders list page."""
        context = super().get_context_data(**kwargs)
        
        # Get current library from session
        current_library_id = self.request.session.get('current_library_id')
        if current_library_id:
            try:
                context['current_library'] = Library.objects.get(id=current_library_id)
            except Library.DoesNotExist:
                context['current_library'] = None
        else:
            context['current_library'] = None
            
        return context

class OrderDetailView(LoginRequiredMixin, DetailView):
    """View for displaying details of a specific order."""
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    model = Order
    
    def get_queryset(self):
        """Ensure users can only view their own orders."""
        return Order.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_details'] = OrderDetail.objects.filter(
            order=self.object
        ).select_related('video')
        return context

@method_decorator(require_POST, name='dispatch')
class AddToCartView(LoginRequiredMixin, View):
    """View for adding a video to the user's cart."""
    
    def post(self, request, *args, **kwargs):
        """Handle POST request to add a video to cart."""
        video_id = request.POST.get('video_id')
        resolution = request.POST.get('resolution', 'HD')  # Default to HD
        price = request.POST.get('price', 0)
        
        try:
            price = float(price)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': 'Invalid price format'
            }, status=400)
        
        # Validate the video exists
        try:
            video = Video.objects.get(id=video_id)
        except Video.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Video not found'
            }, status=404)
        
        # Get the current library
        library_id = request.session.get('current_library_id')
        if not library_id:
            # Use the video's library if no current library is set
            library_id = video.library_id
        
        # Get or create a pending order for the current user in this library
        order, created = Order.objects.get_or_create(
            user=request.user,
            payment_status='pending',
            library_id=library_id,
            defaults={'order_date': timezone.now()}
        )
        
        # Check if this video is already in the cart with the same resolution
        order_detail, created = OrderDetail.objects.get_or_create(
            order=order,
            video=video,
            resolution=resolution,
            defaults={
                'price': price,
                'download_status': 'pending'
            }
        )
        
        if not created:
            # Already in cart, update the price if needed
            if order_detail.price != price:
                order_detail.price = price
                order_detail.save(update_fields=['price'])
        
        # Update the order total
        order.calculate_total()
        
        return JsonResponse({
            'success': True,
            'message': 'Video added to cart',
            'cart_count': OrderDetail.objects.filter(order=order).count()
        })

@method_decorator(require_POST, name='dispatch')
class RemoveFromCartView(LoginRequiredMixin, View):
    """View for removing a video from the user's cart."""
    
    def post(self, request, *args, **kwargs):
        """Handle POST request to remove an item from cart."""
        order_detail_id = request.POST.get('order_detail_id')
        
        try:
            # Ensure the order detail belongs to the current user
            order_detail = OrderDetail.objects.get(
                id=order_detail_id,
                order__user=request.user,
                order__payment_status='pending'
            )
            
            # Delete the order detail
            order_detail.delete()
            
            # Update the order total
            order_detail.order.calculate_total()
            
            return JsonResponse({
                'success': True,
                'message': 'Item removed from cart',
                'cart_count': OrderDetail.objects.filter(order=order_detail.order).count()
            })
            
        except OrderDetail.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Item not found in cart'
            }, status=404)

class CheckoutView(LoginRequiredMixin, View):
    """View for processing the checkout and payment."""
    template_name = 'orders/checkout.html'
    
    def get(self, request, *args, **kwargs):
        """Display the checkout page."""
        # Get the current pending order
        try:
            library_id = request.session.get('current_library_id')
            if not library_id:
                try:
                    library = Library.objects.get(name='Paletta')
                    library_id = library.id
                except Library.DoesNotExist:
                    messages.error(request, "No active library found")
                    return redirect('home')
            
            order = Order.objects.get(
                user=request.user,
                payment_status='pending',
                library_id=library_id
            )
            
            # Get the order details
            order_details = OrderDetail.objects.filter(order=order).select_related('video')
            
            if not order_details.exists():
                messages.warning(request, "Your cart is empty")
                return redirect('cart')
            
            # Calculate the total
            total = sum(detail.price for detail in order_details)
            
            return render(request, self.template_name, {
                'order': order,
                'order_details': order_details,
                'total': total
            })
            
        except Order.DoesNotExist:
            messages.info(request, "You don't have any pending orders")
            return redirect('home')
    
    def post(self, request, *args, **kwargs):
        """Process the payment and finalize the order."""
        # This would integrate with a payment gateway in a real application
        # For now, we'll simulate a successful payment
        
        try:
            library_id = request.session.get('current_library_id')
            if not library_id:
                try:
                    library = Library.objects.get(name='Paletta')
                    library_id = library.id
                except Library.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'No active library'}, status=400)
            
            order = Order.objects.get(
                user=request.user,
                payment_status='pending',
                library_id=library_id
            )
            
            # Update order status
            order.payment_status = 'completed'
            order.save()
            
            # Process each order detail
            for detail in order.details.all():
                # Set download status to processing
                detail.download_status = 'processing'
                detail.save()
                
                # In a real app, trigger the video download preparation here
                # For now, we'll just pretend it's done
            
            return JsonResponse({
                'success': True,
                'message': 'Order completed successfully',
                'redirect_url': reverse('order_detail', kwargs={'pk': order.id})
            })
            
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'No pending order found'}, status=404)

class AddToCollectionView(LoginRequiredMixin, View):
    """View for adding a video to the user's collection (client-side collection)."""
    
    def post(self, request, *args, **kwargs):
        """Handle the POST request to add a video to the collection."""
        try:
            # Get clip_id from POST data
            clip_id = request.POST.get('clip_id')
            
            if not clip_id:
                return JsonResponse({
                    'success': False,
                    'error': 'No clip ID provided'
                }, status=400)
            
            # Get the video to validate it exists
            try:
                video = Video.objects.get(id=clip_id)
            except Video.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Video not found'
                }, status=404)
            
            # We don't actually store this in the database
            # Instead we send a successful response that the client-side JS
            # will use to store the video in localStorage
            
            return JsonResponse({
                'success': True,
                'message': 'Video added to collection',
                'video': {
                    'id': video.id,
                    'title': video.title,
                    'description': video.description,
                    'thumbnail': video.thumbnail.url if video.thumbnail else None
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

class RemoveFromCollectionView(LoginRequiredMixin, View):
    """View for removing a video from the user's collection (client-side collection)."""
    
    def post(self, request, *args, **kwargs):
        """Handle the POST request to remove a video from the collection."""
        try:
            # Get clip_id from POST data
            clip_id = request.POST.get('clip_id')
            
            if not clip_id:
                return JsonResponse({
                    'success': False,
                    'error': 'No clip ID provided'
                }, status=400)
            
            # We don't need to check if it's in the collection since 
            # the collection is stored client-side in localStorage
            
            return JsonResponse({
                'success': True,
                'message': 'Video removed from collection'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500) 