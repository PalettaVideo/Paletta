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
