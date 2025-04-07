from rest_framework import viewsets, permissions, status
from ..models import Category, Video
from ..serializers import CategorySerializer, VideoSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from ..tasks import generate_and_send_download_link
import logging
from ..services import VideoLogService
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

logger = logging.getLogger(__name__)

@method_decorator(never_cache, name='list')
@method_decorator(never_cache, name='retrieve')
class CategoryViewSet(viewsets.ModelViewSet):
    """
    API viewset for managing video categories.
    Provides CRUD operations for categories.
    
    Query parameters:
    - library: Filter categories by library ID
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        """
        Filter categories based on query parameters.
        If library ID is provided, filter categories by that library.
        If no library ID is provided, use the current library from session.
        """
        queryset = super().get_queryset()
        
        # Get library ID from query parameter
        library_id = self.request.query_params.get('library', None)
        
        # If library ID is provided in the request, filter by it
        if library_id:
            queryset = queryset.filter(library_id=library_id)
        # Otherwise, try to get the current library from session
        elif self.request.session.get('current_library_id'):
            library_id = self.request.session.get('current_library_id')
            queryset = queryset.filter(library_id=library_id)
        
        # Add library information to the log for debugging
        if library_id:
            logger.debug(f"Filtering categories by library_id: {library_id}")
        else:
            logger.debug("No library_id filter applied to categories query")
            
        return queryset
    
    def get_serializer_context(self):
        """
        Add request to serializer context for generating absolute URLs
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def finalize_response(self, request, response, *args, **kwargs):
        """
        Add cache control headers to all responses from this viewset
        """
        response = super().finalize_response(request, response, *args, **kwargs)
        
        # Set cache control headers for better client-side caching behavior
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response
    
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
    
    def create(self, request, *args, **kwargs):
        """
        Create a new category.
        If library_id is provided in the form data, use it.
        Otherwise, use the current library from session.
        """
        try:
            # Get library ID from request data
            library_id = request.data.get('library_id')
            
            # If no library ID is provided in the request, try to get from session
            if not library_id:
                library_id = request.session.get('current_library_id')
            
            # If still no library ID, return error
            if not library_id:
                return Response(
                    {"detail": "No library specified for category. Please select a library first."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get library
            from libraries.models import Library
            try:
                library = Library.objects.get(id=library_id)
            except Library.DoesNotExist:
                return Response(
                    {"detail": f"Library with ID {library_id} not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Add library to request data for serializer
            data = request.data.copy()
            data['library'] = library.id
            
            # Create serializer with updated data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            # Log the creation
            logger.info(f"Category '{serializer.instance.name}' created for library '{library.name}' (ID: {library.id})")
            
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
            
        except Exception as e:
            logger.error(f"Error creating category: {str(e)}")
            return Response(
                {"detail": f"Failed to create category: {str(e)}"},
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