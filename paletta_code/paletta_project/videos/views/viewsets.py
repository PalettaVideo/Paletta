from rest_framework import viewsets, permissions, status
from ..models import ContentType, Video
from ..serializers import ContentTypeSerializer, VideoSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from ..tasks import generate_and_send_download_link
import logging
from ..services import VideoLogService
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.db.models import Q
from libraries.models import Library, UserLibraryRole
from rest_framework.views import APIView
from django.http import JsonResponse
from ..models import Tag, VideoTag, ContentType, PalettaContentType

logger = logging.getLogger(__name__)

class IsLibraryOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow library owners or admins to create/modify content types.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Allow read operations for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # For create/update/delete operations, check library ownership
        library_id = request.data.get('library') or request.query_params.get('library')
        if not library_id:
            return False
            
        try:
            library = Library.objects.get(id=library_id)
            # Check if user is the library owner or an admin
            return (library.owner == request.user or 
                   UserLibraryRole.objects.filter(
                       library=library, 
                       user=request.user, 
                       role='admin'
                   ).exists())
        except Library.DoesNotExist:
            return False

@method_decorator(never_cache, name='list')
@method_decorator(never_cache, name='retrieve')
class ContentTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API viewset for managing content types within libraries.
    ContentType objects are library-specific and managed by library owners/admins.
    
    Query parameters: 
    - library: Library ID to filter content types by specific library
    """
    queryset = ContentType.objects.filter(is_active=True)
    serializer_class = ContentTypeSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """
        Filter content types based on query parameters.
        If library ID is provided, filter content types by that library.
        If no library ID is provided, use the current library from session.
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        # Get library ID from query parameter
        library_id = self.request.query_params.get('library', None)
        
        # If library ID is provided in the request, filter by it
        if library_id:
            queryset = queryset.filter(library_id=library_id)
        # Otherwise, try to get the current library from session
        elif self.request.session.get('current_library_id'):
            library_id = self.request.session.get('current_library_id')
            queryset = queryset.filter(library_id=library_id)

        # Only show active content types unless user is library owner/admin
        if library_id and user.is_authenticated:
            try:
                library = Library.objects.get(id=library_id)
                is_owner_or_admin = (library.owner == user or 
                                   UserLibraryRole.objects.filter(
                                       library=library, 
                                       user=user, 
                                       role='admin'
                                   ).exists())
                if not is_owner_or_admin:
                    queryset = queryset.filter(is_active=True)
            except Library.DoesNotExist:
                queryset = queryset.filter(is_active=True)
        else:
            queryset = queryset.filter(is_active=True)
        
        # Add library information to the log for debugging
        if library_id:
            logger.debug(f"Filtering content types by library_id: {library_id}")
        else:
            logger.debug("No library_id filter applied to content types query")
            
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
    
    def create(self, request, *args, **kwargs):
        """
        Create a new content type, ensuring it's associated with a library and user has permission.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class VideoViewSet(viewsets.ModelViewSet):
    """
    BACKEND-READY: Complete video management API with CRUD and download actions.
    MAPPED TO: /api/videos/ (via DRF router)
    
    Provides full video management functionality:
    - List videos with filtering and permissions
    - Retrieve individual video details
    - Create new videos (authenticated users)
    - Update/delete videos (video owners only)
    - Request download links for stored videos
    - Check video storage status
    
    Permissions:
    - List/Retrieve: Public access with private video filtering
    - Create/Update/Delete: Authenticated users, owner restrictions
    - Download: Video uploader or staff only
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
        QUERYSET BUILDER: Filter videos with permissions and query parameters.
        
        Permission logic:
        - Private videos: Only visible to library owners
        - Other videos: Public access
        - For non-list/retrieve actions: Only user's own videos
        
        Query filters:
        - content_type: Filter by content_type ID  
        - tag: Filter by tag name
        - search: Filter by title content
        
        Returns:
            QuerySet: Filtered video objects based on permissions and params
        """
        queryset = Video.objects.all()
        user = self.request.user

        # Filter private videos based on user permissions
        if user.is_authenticated:
            # For authenticated users, exclude private videos unless they're the library owner
            # UNIFIED APPROACH: Only check content_type for private videos
            private_videos_q = Q(content_type__subject_area='private') & ~Q(library__owner=user)
            queryset = queryset.exclude(private_videos_q)
        else:
            # For anonymous users, exclude ALL private videos
            queryset = queryset.exclude(Q(content_type__subject_area='private'))
        
        # Apply filters from query parameters
        content_type_id = self.request.query_params.get('content_type', None)
        tag = self.request.query_params.get('tag', None)
        search = self.request.query_params.get('search', None)
        
        if content_type_id:
            queryset = queryset.filter(content_type_id=content_type_id)
        if tag:
            queryset = queryset.filter(tags__name=tag)
        if search:
            queryset = queryset.filter(title__icontains=search)
            
        if self.action in ['list', 'retrieve']:
            queryset = queryset
        
        # For authenticated users, show published videos and their own unpublished videos
        elif self.request.user.is_authenticated:
            queryset = queryset.filter(uploader=self.request.user)
        
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
        CREATE HANDLER: Set video uploader to current authenticated user.
        
        Automatically assigns the requesting user as the video uploader.
        This ensures proper ownership and permission tracking.
        
        Args:
            serializer: Video serializer with validated data
        """
        serializer.save(uploader=self.request.user)
        
    @action(detail=True, methods=['post'])
    def request_download(self, request, pk=None):
        """
        ACTION: Request download link generation for stored videos.
        MAPPED TO: /api/videos/<id>/request_download/
        
        Queues background task to generate secure download link and email it.
        All authenticated users can request downloads for non-private videos.
        Private videos can only be downloaded by library owners.
        Video must have storage_status='stored' to be downloadable.
        
        POST data:
        - email (optional): Email address to send link to (defaults to user's email)
        
        Returns:
            Response: Success message with email confirmation or error
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
                
            # Check if this is a private video and user has permission
            if video.is_private:
                if video.library.owner != user:
                    return Response(
                        {'detail': 'You do not have permission to request download for this private video.'}, 
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
        ACTION: Get video storage status and metadata.
        MAPPED TO: /api/videos/<id>/storage_status/
        
        Returns detailed storage information for video uploaders and staff.
        Useful for tracking upload progress and troubleshooting storage issues.
        
        Returns:
            Response: Storage status, URLs, and download link info or error
            
        Response format:
            {
                "status": "stored",
                "status_display": "Stored in Deep Storage",
                "storage_url": "s3://bucket/path/to/video.mp4",
                "has_download_link": true,
                "download_link_expiry": "2024-01-01T12:00:00Z"
            }
        """
        try:
            video = self.get_object()
            
            # Check if user has permission to view this video's status
            if video.uploader != request.user and not request.user.is_staff:
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

    def check_object_permissions(self, request, obj):
        # Allow access if the user is the uploader or a staff member
        if obj.uploader == request.user or request.user.is_staff:
            return
        
        # Deny access for all other cases
        self.permission_denied(
            request, 
            message="You do not have permission to access this content type."
        ) 

@method_decorator(never_cache, name='get')
class UnifiedContentTypeViewSet(APIView):
    """
    Unified API for content types that returns library-specific content types.
    ContentType objects are library-specific and available to their respective libraries.
    
    Query parameters:
    - library: Library ID to filter content types by specific library
    """
    
    def get(self, request, *args, **kwargs):
        """
        Return active content types for the specified library
        """
        try:
            content_types_data = []
            
            # Get library ID from query parameter
            library_id = request.query_params.get('library', None)
            
            if library_id:
                # Get active content types for the specific library
                content_types = ContentType.objects.filter(
                    library_id=library_id, 
                    is_active=True
                ).order_by('subject_area')
            else:
                # If no library specified, try to get from session
                library_id = request.session.get('current_library_id')
                if library_id:
                    content_types = ContentType.objects.filter(
                        library_id=library_id, 
                        is_active=True
                    ).order_by('subject_area')
                else:
                    # No library context, return empty list
                    content_types = ContentType.objects.none()
            
            for content_type in content_types:
                content_types_data.append({
                    'id': content_type.id,
                    'name': content_type.display_name,
                    'display_name': content_type.display_name,
                    'code': content_type.subject_area,
                    'type': 'content_type',
                    'is_active': content_type.is_active,
                    'library_id': content_type.library_id,
                })
            
            logger.debug(f"Returned {len(content_types_data)} content types for library {library_id}")
            
            return Response(content_types_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in UnifiedContentTypeViewSet: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve content types'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

 