from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
import logging

from .models import Order, OrderDetail, DownloadRequest
from .services import DownloadRequestService
from videos.models import Video
from libraries.models import Library

logger = logging.getLogger(__name__)

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
    """View for displaying a user's download request history."""
    template_name = 'orders/orders_list.html'
    context_object_name = 'download_requests'
    
    def get_queryset(self):
        """Return all download requests for the current user, grouped by request date."""
        return DownloadRequest.objects.filter(
            user=self.request.user
        ).select_related('video', 'video__library').order_by('-request_date')

    def get_context_data(self, **kwargs):
        """Group download requests by date and add library context."""
        context = super().get_context_data(**kwargs)
        
        # Group download requests by date (same day requests are grouped together)
        from itertools import groupby
        from operator import attrgetter
        
        download_requests = context['download_requests']
        grouped_requests = {}
        
        for request in download_requests:
            # Create a key based on date and user for grouping
            date_key = request.request_date.strftime('%Y-%m-%d')
            if date_key not in grouped_requests:
                grouped_requests[date_key] = {
                    'date': request.request_date,
                    'requests': [],
                    'order_number': len(grouped_requests) + 1  # Simple order numbering
                }
            grouped_requests[date_key]['requests'].append(request)
        
        context['grouped_requests'] = grouped_requests
        
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
    """View for processing download requests from cart items."""
    template_name = 'orders/checkout.html'
    
    def get(self, request, *args, **kwargs):
        """Display the download request page with cart items."""
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
            
            # Get the order details with video information
            order_details = OrderDetail.objects.filter(order=order).select_related('video')
            
            if not order_details.exists():
                messages.warning(request, "Your cart is empty")
                return redirect('cart')
            
            # Filter out videos that are not available for download
            available_details = []
            for detail in order_details:
                if detail.video.storage_status == 'stored':
                    available_details.append(detail)
                else:
                    logger.warning(f"Video {detail.video.id} not available for download (status: {detail.video.storage_status})")
            
            if not available_details:
                messages.warning(request, "No videos in your cart are currently available for download")
                return redirect('cart')
            
            return render(request, self.template_name, {
                'order': order,
                'order_details': available_details,
                'total_videos': len(available_details)
            })
            
        except Order.DoesNotExist:
            messages.info(request, "You don't have any pending orders")
            return redirect('home')
    
    def post(self, request, *args, **kwargs):
        """Handle download request processing (not used - downloads handled by API)."""
        # This method is kept for compatibility but the actual download requests
        # are handled by the bulk_download_request API endpoint via JavaScript
        return JsonResponse({
            'success': False, 
            'message': 'Download requests should use the bulk download API endpoint'
        }, status=400)

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

# ==============================================================================
# DOWNLOAD REQUEST API VIEWS
# ==============================================================================

class DownloadRequestAPIView(APIView):
    """
    BACKEND-READY: Main download request endpoint for video downloads.
    MAPPED TO: POST /api/request-download/
    USED BY: Frontend download request functionality, cart checkout flow
    
    Validates user permissions, creates download request, generates S3 presigned URL.
    Triggers email automation with 48-hour valid download link.
    Implements idempotency to prevent duplicate requests.
    Required fields: video_id (int), email (str, optional)
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, format=None):
        """
        POST HANDLER: Create and process video download request.
        
        Request data expected:
        - video_id (int): ID of video to download
        - email (str, optional): Email address for download link (defaults to user's email)
        
        Returns:
            Response: Success message with request details or error information
        """
        try:
            video_id = request.data.get('video_id')
            email = request.data.get('email', request.user.email)
            
            # Validate required fields
            if not video_id:
                return Response({
                    'error': 'video_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate email format
            if not email or '@' not in email:
                return Response({
                    'error': 'Valid email address is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get the video
            try:
                video = Video.objects.get(id=video_id)
            except Video.DoesNotExist:
                return Response({
                    'error': 'Video not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check user permissions for private videos
            if video.is_private and video.library.owner != request.user:
                return Response({
                    'error': 'You do not have permission to download this private video'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if video is stored and available
            if video.storage_status != 'stored':
                return Response({
                    'error': f'Video is not available for download (status: {video.get_storage_status_display()})',
                    'video_status': video.storage_status
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create download request using service
            download_service = DownloadRequestService()
            
            try:
                download_request = download_service.create_download_request(
                    user=request.user,
                    video=video,
                    email=email
                )
                
                # Process the request (generate URL and send email)
                success = download_service.process_download_request(download_request)
                
                if success:
                    logger.info(f"Successfully processed download request {download_request.id} for user {request.user.email}")
                    return Response({
                        'success': True,
                        'message': f'Download link has been sent to {email}',
                        'request_id': download_request.id,
                        'expiry_date': download_request.expiry_date.isoformat(),
                        'video_title': video.title
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'error': 'Failed to process download request. Please try again.',
                        'request_id': download_request.id
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            except ValueError as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Failed to create download request for user {request.user.email}, video {video_id}: {str(e)}")
                return Response({
                    'error': 'Internal server error while processing download request'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Unexpected error in download request API: {str(e)}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DownloadRequestStatusAPIView(APIView):
    """
    BACKEND-READY: Check status of download requests.
    MAPPED TO: GET /api/download-requests/
    USED BY: Frontend status checking, user dashboard
    
    Returns user's download request history with status and expiry information.
    Allows filtering by status and provides pagination support.
    Required permissions: authenticated user
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, format=None):
        """
        GET HANDLER: Retrieve user's download request history.
        
        Query parameters:
        - status (str, optional): Filter by request status
        - limit (int, optional): Limit number of results (default: 10)
        
        Returns:
            Response: List of download requests with status and expiry info
        """
        try:
            status_filter = request.query_params.get('status')
            limit = int(request.query_params.get('limit', 10))
            
            # Get user's download requests
            queryset = DownloadRequest.objects.filter(user=request.user)
            
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            requests = queryset.order_by('-request_date')[:limit]
            
            # Serialize the data
            request_data = []
            for req in requests:
                request_data.append({
                    'id': req.id,
                    'video_title': req.video.title,
                    'video_id': req.video.id,
                    'status': req.status,
                    'status_display': req.get_status_display(),
                    'email': req.email,
                    'request_date': req.request_date.isoformat(),
                    'expiry_date': req.expiry_date.isoformat(),
                    'is_expired': req.is_expired(),
                    'email_sent': req.email_sent,
                    'library_name': req.video.library.name if req.video.library else None
                })
            
            return Response({
                'requests': request_data,
                'total_count': queryset.count()
            }, status=status.HTTP_200_OK)
            
        except ValueError:
            return Response({
                'error': 'Invalid limit parameter'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error retrieving download requests for user {request.user.email}: {str(e)}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResendDownloadEmailAPIView(APIView):
    """
    BACKEND-READY: Resend download email for existing requests.
    MAPPED TO: POST /api/download-requests/<id>/resend/
    USED BY: User dashboard, admin resend functionality
    
    Resends email for valid download requests within expiry period.
    Prevents resending for expired or failed requests.
    Required permissions: authenticated user (own requests only)
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, request_id, format=None):
        """
        POST HANDLER: Resend download email for specific request.
        
        URL parameters:
        - request_id (int): ID of the download request to resend
        
        Returns:
            Response: Success message or error information
        """
        try:
            # Get the download request (user can only access their own)
            try:
                download_request = DownloadRequest.objects.get(
                    id=request_id,
                    user=request.user
                )
            except DownloadRequest.DoesNotExist:
                return Response({
                    'error': 'Download request not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if request is still valid
            if download_request.is_expired():
                return Response({
                    'error': 'Download request has expired. Please create a new request.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if download_request.status == 'failed':
                return Response({
                    'error': 'Cannot resend email for failed request. Please create a new request.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Resend email using service
            download_service = DownloadRequestService()
            success = download_service.send_download_email(download_request)
            
            if success:
                return Response({
                    'success': True,
                    'message': f'Download email resent to {download_request.email}'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Failed to resend email. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error resending download email for request {request_id}: {str(e)}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def bulk_download_request(request):
    """
    BACKEND-READY: Create multiple download requests from cart/order.
    MAPPED TO: POST /api/bulk-download-request/
    USED BY: Cart checkout flow, bulk download functionality
    
    Processes multiple video download requests in a single API call.
    Useful for cart-based workflows where users select multiple videos.
    Required fields: video_ids (list), email (str, optional)
    """
    try:
        video_ids = request.data.get('video_ids', [])
        email = request.data.get('email', request.user.email)
        
        if not video_ids or not isinstance(video_ids, list):
            return Response({
                'error': 'video_ids must be a non-empty list'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(video_ids) > 10:  # Limit bulk requests
            return Response({
                'error': 'Cannot request more than 10 videos at once'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        download_service = DownloadRequestService()
        results = []
        download_requests = []
        
        # First pass: create download requests for valid videos
        for video_id in video_ids:
            try:
                video = Video.objects.get(id=video_id)
                
                # Check permissions and availability
                if video.is_private and video.library.owner != request.user:
                    results.append({
                        'video_id': video_id,
                        'video_title': video.title,
                        'success': False,
                        'error': 'Permission denied for private video'
                    })
                    continue
                
                if video.storage_status != 'stored':
                    results.append({
                        'video_id': video_id,
                        'video_title': video.title,
                        'success': False,
                        'error': f'Video not available (status: {video.get_storage_status_display()})'
                    })
                    continue
                
                # Create download request (don't process individually)
                download_request = download_service.create_download_request(
                    user=request.user,
                    video=video,
                    email=email
                )
                
                download_requests.append(download_request)
                results.append({
                    'video_id': video_id,
                    'video_title': video.title,
                    'success': True,
                    'request_id': download_request.id,
                    'status': 'pending_manager_review'
                })
                    
            except Video.DoesNotExist:
                results.append({
                    'video_id': video_id,
                    'success': False,
                    'error': 'Video not found'
                })
            except Exception as e:
                logger.error(f"Error creating download request for video {video_id}: {str(e)}")
                results.append({
                    'video_id': video_id,
                    'success': False,
                    'error': 'Internal error processing request'
                })
        
        # Second pass: send single manager notification for all valid requests
        successful_requests = len(download_requests)
        if download_requests:
            try:
                bulk_success = download_service.process_bulk_download_request(download_requests)
                if not bulk_success:
                    logger.error(f"Failed to send bulk manager notification for {len(download_requests)} requests")
                    # Mark all as failed in results
                    for result in results:
                        if result.get('success'):
                            result['success'] = False
                            result['error'] = 'Failed to notify manager'
                    successful_requests = 0
            except Exception as e:
                logger.error(f"Error in bulk download processing: {str(e)}")
                # Mark all as failed in results
                for result in results:
                    if result.get('success'):
                        result['success'] = False
                        result['error'] = 'Failed to process bulk request'
                successful_requests = 0
        
        return Response({
            'success': successful_requests > 0,
            'message': f'Successfully submitted {successful_requests} of {len(video_ids)} video download requests for manager review',
            'email': email,
            'results': results,
            'successful_count': successful_requests,
            'total_count': len(video_ids),
            'manager_notification': successful_requests > 0
        }, status=status.HTTP_200_OK if successful_requests > 0 else status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error in bulk download request: {str(e)}")
        return Response({
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 