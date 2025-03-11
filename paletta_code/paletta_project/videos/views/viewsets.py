from rest_framework import viewsets, permissions, status
from ..models import Category, Video
from ..serializers import CategorySerializer, VideoSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from ..tasks import generate_and_send_download_link
import logging
from ..services import VideoLogService

logger = logging.getLogger(__name__)

class CategoryViewSet(viewsets.ModelViewSet):
    """
    API viewset for managing video categories.
    Provides CRUD operations for categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_serializer_context(self):
        """
        Add request to serializer context for generating absolute URLs
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=True, methods=['get'])
    def image(self, request, pk=None):
        """
        Return the image URL for a specific category
        """
        try:
            category = self.get_object()
            if category.image:
                image_url = request.build_absolute_uri(category.image.url)
                return Response({'image_url': image_url})
            return Response({'image_url': None})
        except Exception as e:
            logger.error(f"Error in category image action: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve category image'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VideoViewSet(viewsets.ModelViewSet):
    """
    API viewset for managing videos.
    Provides CRUD operations for videos and additional actions for download links.
    """
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    
    def get_serializer_context(self):
        """
        Add request to serializer context for generating absolute URLs
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        """
        Filter videos based on query parameters and user permissions
        """
        queryset = Video.objects.all()
        
        # Apply filters from query parameters
        category_id = self.request.query_params.get('category', None)
        tag = self.request.query_params.get('tag', None)
        search = self.request.query_params.get('search', None)
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if tag:
            queryset = queryset.filter(tags__name=tag)
        if search:
            queryset = queryset.filter(title__icontains=search)
            
        # Only show published videos to non-owners
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_published=True)
        else:
            # If authenticated but not filtering for own videos, show published + own
            user_filter = self.request.query_params.get('user', None)
            if not user_filter or int(user_filter) != self.request.user.id:
                queryset = queryset.filter(is_published=True) | queryset.filter(uploader=self.request.user)
        
        return queryset
    
    def get_permissions(self):
        """
        Allow anyone to view videos, but only authenticated users to modify
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """
        Set the uploader to the current user when creating a video
        """
        serializer.save(uploader=self.request.user)
        
    @action(detail=True, methods=['post'])
    def request_download(self, request, pk=None):
        """
        Request a download link for a video.
        The link will be sent to the user's email address.
        """
        try:
            video = self.get_object()
            user = request.user
            
            # Check if user is authenticated
            if not user.is_authenticated:
                return Response(
                    {"error": "Authentication required to request download links."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
                
            # Check if user has permission to download this video
            if not video.is_published and video.uploader != user:
                return Response(
                    {"error": "You don't have permission to download this video."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if the video is stored in AWS S3 storage
            if video.storage_status != 'stored':
                return Response(
                    {"error": "This video is not available for download yet.", "status": video.storage_status},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get email from request or use user's email
            email = request.data.get('email', user.email)
            if not email:
                return Response(
                    {"error": "No email address provided for sending the download link."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Queue task to generate and send download link
            generate_and_send_download_link.delay(video.id, email)
            
            # Log the download request
            VideoLogService.log_download(video, user, request)
            
            return Response({
                "message": "Download link will be sent to your email shortly.",
                "email": email
            })
            
        except Exception as e:
            logger.error(f"Error in request_download action: {str(e)}")
            return Response(
                {"error": "Failed to process download request."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def storage_status(self, request, pk=None):
        """
        Get the storage status of a video.
        """
        try:
            video = self.get_object()
            
            # Check if user has permission to view this video's status
            if not video.is_published and video.uploader != request.user and not request.user.is_staff:
                return Response(
                    {"error": "You don't have permission to view this video's status."},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            return Response({
                "status": video.storage_status,
                "status_display": dict(Video.STORAGE_STATUS_CHOICES).get(video.storage_status, video.storage_status),
                "storage_url": video.storage_url,
                "has_download_link": bool(video.download_link),
                "download_link_expiry": video.download_link_expiry
            })
            
        except Exception as e:
            logger.error(f"Error in storage_status action: {str(e)}")
            return Response(
                {"error": "Failed to retrieve storage status."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 