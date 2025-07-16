from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics, parsers
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q
from ..models import Video, ContentType, Tag, VideoTag
from ..serializers import VideoSerializer, TagSerializer
from libraries.models import Library
import logging
import urllib.parse
from django.conf import settings

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for API results, showing 12 items per page.
    """
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100


class VideoFilterMixin:
    """
    UTILITY MIXIN: Consolidated filtering logic to eliminate code duplication.
    
    Provides common video filtering logic across multiple API views.
    Only includes filters that are actually used by the frontend.
    Note: No 'published' status filtering - videos are either uploaded or failed.
    """
    
    def apply_video_filters(self, queryset, request):
        """
        CORE FILTERING: Apply common video filters to a queryset.
        
        Applied filters:
        - Search: Filter by video title/description content
        - Sorting: Order by upload date or popularity
        
        Args:
            queryset (QuerySet): Django QuerySet to filter
            request (HttpRequest): HTTP request containing query parameters
            
        Returns:
            QuerySet: Filtered and ordered video queryset
        """
        # Search filter (USED: by frontend search functionality)
        search_query = request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # Sorting (USED: by frontend sort dropdown)
        sort_by = request.query_params.get('sort_by', 'newest')
        sort_mapping = {
            'newest': '-upload_date',
            'oldest': 'upload_date', 
            'popular': '-views_count',
        }
        
        if sort_by in sort_mapping:
            queryset = queryset.order_by(sort_mapping[sort_by])
        else:
            queryset = queryset.order_by('-upload_date')  # Default
        
        return queryset.distinct()


# ==============================================================================
# FRONTEND-READY ENDPOINTS (Used by JavaScript with current features set)
# ==============================================================================

class VideoAPIUploadView(APIView):
    """
    FRONTEND-READY: Main video upload endpoint for metadata creation.
    MAPPED TO: /api/upload/
    USED BY: upload.js line 635
    
    Creates video database record after successful S3 upload completes.
    This is the final step in the upload process flow:
    1. Frontend uploads file directly to S3 using presigned URL
    2. Frontend calls this endpoint with S3 key and metadata
    3. This endpoint creates the Video record with storage_status='stored'
    
    Required fields: s3_key, title, content_type, library_id
    Optional fields: description, tags, duration, file_size, format, thumbnail
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    
    def post(self, request, format=None):
        """
        POST HANDLER: Create video record after S3 upload completion.
        
        Request data expected:
        - s3_key (str): AWS S3 key where video is stored
        - title (str): Video title
        - content_type (int): Content type ID for primary classification
        - library_id (int): Library ID where video belongs
        - description (str, optional): Video description
        - tags (str, optional): Comma-separated tag names
        - duration (int, optional): Video duration in seconds
        - file_size (int, optional): File size in bytes
        - format (str, optional): Video format (mp4, mov, etc.)
        - thumbnail (file, optional): Thumbnail image file
        
        Returns:
            Response: Video data with 201 status on success, error on failure
        """
        s3_key = request.data.get('s3_key')
        if not s3_key:
            return Response({'message': 's3_key is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # Get required data from request
            title = request.data.get('title', 'Untitled Video')
            description = request.data.get('description', '')
            content_type_id = request.data.get('content_type')
            library_id = request.data.get('library_id')
            tags_str = request.data.get('tags', '')
            duration = request.data.get('duration')
            file_size = request.data.get('file_size')
            format_type = request.data.get('format')
            thumbnail = request.FILES.get('thumbnail')
            
            # Content type validation (1 required)
            if not content_type_id:
                return Response({'message': 'Content type is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate library and content type
            try:
                library = Library.objects.get(id=library_id)
            except Library.DoesNotExist:
                return Response({'message': 'Library not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Validate content type belongs to the library
            try:
                content_type = ContentType.objects.get(id=content_type_id, library=library, is_active=True)
            except ContentType.DoesNotExist:
                return Response({'message': f"Content type with id {content_type_id} not found in this library"}, status=status.HTTP_404_NOT_FOUND)
            
            # Create video record
            video = Video.objects.create(
                title=title,
                description=description,
                content_type=content_type,
                library=library,
                uploader=request.user,
                storage_reference_id=s3_key,
                storage_url=f"s3://{settings.AWS_STORAGE_BUCKET_NAME}/{s3_key}",
                storage_status='stored',
                duration=duration,
                file_size=file_size,
                format=format_type
            )
            
            # Set thumbnail if provided
            if thumbnail:
                video.thumbnail = thumbnail
                video.save(update_fields=['thumbnail'])
                
            # Handle tags
            if tags_str:
                tag_names = [name.strip() for name in tags_str.split(',') if name.strip()]
                for tag_name in tag_names:
                    tag, _ = Tag.objects.get_or_create(name=tag_name, library=library)
                    VideoTag.objects.create(video=video, tag=tag)
                    
            serializer = VideoSerializer(video, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Error in VideoAPIUploadView: {e}")
            return Response({'message': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PopularTagsAPIView(APIView):
    """
    FRONTEND-READY: Get popular tags for video filtering interface.
    MAPPED TO: /api/popular-tags/
    
    Returns the top 20 most popular tags based on video count.
    Used by frontend filtering components to show popular tag options.
    Tags are ordered by video count (descending).
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, format=None):
        """
        GET HANDLER: Retrieve top 20 popular tags ordered by video count.
        
        No parameters required.
        
        Returns:
            Response: List of tag objects with video counts, or error message
            
        Response format:
            [
                {
                    "id": 1,
                    "name": "campus life",
                    "library": 1,
                    "videos_count": 15
                }
            ]
        """
        try:
            # Get the top 20 tags with the most videos
            tags = Tag.objects.annotate(
                videos_count=Count('videos')
            ).order_by('-videos_count')[:20]
            
            serializer = TagSerializer(tags, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving popular tags: {str(e)}")
            return Response(
                {"error": "Unable to retrieve popular tags"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ==============================================================================
# BACKEND-READY ENDPOINTS (URL mapped for future feature implementations)
# ==============================================================================

class UnifiedVideoListAPIView(generics.ListAPIView, VideoFilterMixin):
    """
    BACKEND-READY: Unified video listing with optional content type filtering.
    MAPPED TO: /api/videos/ and /api/content-types/<name>/videos/
    
    Consolidates VideoListAPIView and ContentTypeVideosAPIView into one endpoint.
    Returns paginated list of videos with optional content type filtering.
    
    URL patterns:
    - /api/videos/ - All videos
    - /api/content-types/<content_type_name>/videos/ - Videos in specific content type
    
    Query parameters:
    - search: Filter by title/description content
    - sort_by: 'newest', 'oldest', or 'popular'
    - page: Page number for pagination
    """
    serializer_class = VideoSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """
        QUERYSET BUILDER: Get videos with optional content type filtering.
        
        Content type filtering logic:
        1. If content_type_name in URL kwargs, filter by that content type
        2. Handles both subject areas and content types
        3. Decodes URL encoding and converts hyphens to spaces
        4. Returns empty queryset if content type not found
        
        Returns:
            QuerySet: Video objects filtered by content type (if specified) and common filters
        """
        queryset = Video.objects.all()
        
        # Content type filtering (if content_type_name is provided in URL)
        content_type_name = self.kwargs.get('content_type_name')
        if content_type_name:
            # Decode URL encoding and handle hyphens vs spaces
            decoded_content_type_name = urllib.parse.unquote(content_type_name)
            db_content_type_name = decoded_content_type_name.replace('-', ' ')
            
            logger.info(f"Content type lookup: '{db_content_type_name}'")
            
            try:
                # Look up content type by subject_area
                content_type = ContentType.objects.get(subject_area__iexact=db_content_type_name.replace(' ', '_'), is_active=True)
                queryset = queryset.filter(content_type=content_type)
            except ContentType.DoesNotExist:
                logger.warning(f"Content type '{db_content_type_name}' not found")
                return Video.objects.none()
        
        # Apply common filters (search, sorting)
        queryset = self.apply_video_filters(queryset, self.request)
        
        return queryset

    def list(self, request, *args, **kwargs):
        """
        LIST HANDLER: Return paginated video list with proper empty response.
        
        Ensures that empty querysets return a valid JSON response with count=0
        instead of causing frontend errors.
        
        Returns:
            Response: Paginated video list or empty array with count
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        if not queryset.exists():
            logger.info("Returning empty results for video list")
            return Response({"count": 0, "results": []})
            
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class VideoDetailAPIView(generics.RetrieveAPIView):
    """
    BACKEND-READY: Get single video details with view count increment.
    MAPPED TO: /api/videos/<video_id>/
    
    Retrieves detailed information for a specific video by ID.
    Automatically increments the video's view count on each access.
    Returns full video data including metadata, tags, and URLs.
    """
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [permissions.AllowAny]
    lookup_url_kwarg = 'video_id'
    
    def retrieve(self, request, *args, **kwargs):
        """
        RETRIEVE HANDLER: Get video details and increment view count.
        
        Side effects:
        - Increments video.views_count by 1
        - Saves the updated count to database
        
        Args:
            video_id (int): Video ID from URL parameter
            
        Returns:
            Response: Video object data or error message
        """
        try:
            instance = self.get_object()
            
            # Increment view count
            instance.views_count += 1
            instance.save(update_fields=['views_count'])
            
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving video details: {str(e)}")
            return Response(
                {"error": "Unable to retrieve video details"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContentTypeVideosAPIView(generics.ListAPIView, VideoFilterMixin):
    """
    BACKEND-READY: Filter videos by content types.
    MAPPED TO: /api/content-type-videos/
    
    Advanced filtering by content type codes or IDs.
    Supports both content type codes ('campus_life') and IDs (1, 2, 3).
    
    Query parameters:
    - content_types: List of content type codes (e.g., campus_life, research_innovation)
    - content_type_ids: List of content type IDs (e.g., 1, 3, 5)
    - search: Filter by title/description
    - sort_by: 'newest', 'oldest', or 'popular'
    """
    serializer_class = VideoSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """
        QUERYSET BUILDER: Filter videos by content types.
        
        Filtering logic:
        1. Get content_types (codes) and content_type_ids from query params
        2. Filter videos by the specified content types
        3. Apply additional common filters (search, sorting)
        
        Returns:
            QuerySet: Videos filtered by content types and other criteria
        """
        queryset = Video.objects.all()
        
        # Content type filtering
        content_types = self.request.query_params.getlist('content_types', [])
        content_type_ids = self.request.query_params.getlist('content_type_ids', [])
        
        if content_types or content_type_ids:
            # Filter by content types
            if content_types:
                queryset = queryset.filter(content_type__subject_area__in=content_types)
            if content_type_ids:
                queryset = queryset.filter(content_type__id__in=content_type_ids)
        
        # Apply common filters
        queryset = self.apply_video_filters(queryset, self.request)
        
        return queryset


# ==============================================================================
# COMPATIBILITY ALIASES (For existing URL patterns)
# ==============================================================================

# These maintain backward compatibility with existing URLs
VideoListAPIView = UnifiedVideoListAPIView
ContentTypeVideosAPIView = UnifiedVideoListAPIView 