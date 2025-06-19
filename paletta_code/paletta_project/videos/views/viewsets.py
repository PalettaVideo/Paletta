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
from django.db.models import Q
from libraries.models import Library, UserLibraryRole
from rest_framework.views import APIView
from django.http import JsonResponse
from ..models import Tag, VideoTag, ContentType, PalettaCategory

logger = logging.getLogger(__name__)

class IsLibraryOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow library owners or admins to create/modify categories.
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
class CategoryViewSet(viewsets.ModelViewSet):
    """
    API viewset for managing predefined video categories.
    Only library owners and admins can create/modify categories.
    Categories use fixed enums for subject areas and content types.
    
    Query parameters:
    - library: Filter categories by library ID
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_permissions(self):
        """
        Set permissions based on action type.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsLibraryOwnerOrAdmin]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Filter categories based on query parameters.
        If library ID is provided, filter categories by that library.
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

        # Only show active categories unless user is library owner/admin
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
    
    def create(self, request, *args, **kwargs):
        """
        Create a new category, ensuring it's associated with a library and user has permission.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=False, methods=['get'])
    def available_combinations(self, request):
        """
        Return all available subject area combinations
        """
        subject_areas = [
            {'code': code, 'display': display} 
            for code, display in Category.SUBJECT_AREA_CHOICES
        ]
        return Response(subject_areas)
    
    @action(detail=False, methods=['get'])
    def subject_areas(self, request):
        """
        Return all available subject areas
        """
        subject_areas = [
            {'code': code, 'display': display} 
            for code, display in Category.SUBJECT_AREA_CHOICES
        ]
        return Response(subject_areas)
    
    @action(detail=False, methods=['get'])
    def content_types(self, request):
        """
        Return all available content types from the ContentType model
        """
        from ..models import ContentType
        content_types = [
            {'code': ct.code, 'display': ct.display_name} 
            for ct in ContentType.objects.filter(is_active=True)
        ]
        return Response(content_types)
    
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
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a category with proper permission checks and response format
        """
        try:
            category = self.get_object()
            
            # Check if user has permission to delete this category
            if category.library.owner != request.user and not UserLibraryRole.objects.filter(
                library=category.library, user=request.user, role='admin'
            ).exists():
                return Response({
                    'status': 'error',
                    'message': 'You do not have permission to delete this category.'
                }, status=403)
            
            # Check if there are videos using this category
            video_count = Video.objects.filter(subject_area=category).count()
            if video_count > 0:
                return Response({
                    'status': 'error',
                    'message': f'Cannot delete category. {video_count} video(s) are using this category. Please reassign or delete those videos first.'
                }, status=400)
            
            category_name = category.display_name
            self.perform_destroy(category)
            
            return Response({
                'status': 'success',
                'message': f'Category "{category_name}" deleted successfully.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error deleting category: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to delete category.'
            }, status=500)

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
        Filter videos based on query parameters and user permissions.
        Hides private videos from users who are not the library owner.
        """
        queryset = Video.objects.all()
        user = self.request.user

        # Filter private videos based on user permissions
        if user.is_authenticated:
            # For authenticated users, exclude private videos unless they're the library owner
            private_videos_q = Q(
                # Private Paletta category videos
                (Q(paletta_category__code='private') & ~Q(library__owner=user)) |
                # Private subject area videos
                (Q(subject_area__subject_area='private') & ~Q(library__owner=user))
            )
            queryset = queryset.exclude(private_videos_q)
        else:
            # For anonymous users, exclude ALL private videos
            queryset = queryset.exclude(
                Q(paletta_category__code='private') | 
                Q(subject_area__subject_area='private')
            )
        
        # Apply filters from query parameters
        category_id = self.request.query_params.get('category', None)
        tag = self.request.query_params.get('tag', None)
        search = self.request.query_params.get('search', None)
        
        if category_id:
            queryset = queryset.filter(subject_area_id=category_id)
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

    def check_object_permissions(self, request, obj):
        # Allow access if the user is the uploader or a staff member
        if obj.uploader == request.user or request.user.is_staff:
            return
        
        # Deny access for all other cases
        self.permission_denied(
            request, 
            message="You do not have permission to access this category."
        ) 

@method_decorator(never_cache, name='get')
class UnifiedCategoryViewSet(APIView):
    """
    Unified API for categories that returns appropriate categories based on library type.
    - For Paletta-style libraries: Returns PalettaCategory objects
    - For custom libraries: Returns Category objects (subject areas)
    
    Query parameters:
    - library: Library ID to filter categories for
    """
    
    def get(self, request, *args, **kwargs):
        """
        Return categories appropriate for the specified library
        """
        try:
            # Get library ID from query parameter
            library_id = request.query_params.get('library', None)
            
            if not library_id:
                return Response(
                    {'error': 'Library ID is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the library
            try:
                library = Library.objects.get(id=library_id)
            except Library.DoesNotExist:
                return Response(
                    {'error': 'Library not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            categories_data = []
            
            if library.uses_paletta_categories:
                # For Paletta-style libraries, return PalettaCategory objects
                paletta_categories = PalettaCategory.objects.filter(is_active=True).order_by('code')
                
                for pc in paletta_categories:
                    categories_data.append({
                        'id': f'paletta_{pc.id}',  # Prefix to distinguish from regular categories
                        'name': pc.display_name,
                        'display_name': pc.display_name,
                        'code': pc.code,
                        'type': 'paletta_category',
                        'library': {
                            'id': library.id,
                            'name': library.name
                        },
                        'is_active': pc.is_active,
                        'description': pc.description or '',
                        'image_url': None,  # PalettaCategory doesn't have images yet
                    })
                
                logger.debug(f"Returned {len(categories_data)} Paletta categories for library {library.name}")
                
            else:
                # For custom libraries, return Category objects (subject areas)
                categories = Category.objects.filter(library=library, is_active=True).order_by('subject_area')
                
                for category in categories:
                    image_url = None
                    if category.image:
                        image_url = request.build_absolute_uri(category.image.url)
                    
                    categories_data.append({
                        'id': category.id,
                        'name': category.display_name,
                        'display_name': category.display_name,
                        'subject_area': category.subject_area,
                        'type': 'subject_area',
                        'library': {
                            'id': library.id,
                            'name': library.name
                        },
                        'is_active': category.is_active,
                        'description': category.description or '',
                        'image_url': image_url,
                        'created_at': category.created_at.isoformat() if category.created_at else None,
                    })
                
                logger.debug(f"Returned {len(categories_data)} custom categories for library {library.name}")
            
            return Response(categories_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in UnifiedCategoryViewSet: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve categories'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(never_cache, name='get')
class ContentTypeViewSet(APIView):
    """
    API for content types - these are global and used by all libraries
    """
    
    def get(self, request, *args, **kwargs):
        """
        Return all available content types
        """
        try:
            content_types = ContentType.objects.filter(is_active=True).order_by('code')
            
            content_types_data = []
            for ct in content_types:
                content_types_data.append({
                    'id': ct.id,
                    'code': ct.code,
                    'name': ct.display_name,
                    'display_name': ct.display_name,
                    'description': ct.description or '',
                    'is_active': ct.is_active,
                })
            
            logger.debug(f"Returned {len(content_types_data)} content types")
            return Response(content_types_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in ContentTypeViewSet: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve content types'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 