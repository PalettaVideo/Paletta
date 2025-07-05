from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics, parsers
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q
from ..models import Video, Category, Tag, VideoTag
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
    
    Required fields: s3_key, title, category, library_id, content_types
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
        - category (int): Category ID for subject area
        - library_id (int): Library ID where video belongs
        - content_types (list): List of content type IDs (1-3 required)
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
            category_id = request.data.get('category')
            library_id = request.data.get('library_id')
            tags_str = request.data.get('tags', '')
            duration = request.data.get('duration')
            file_size = request.data.get('file_size')
            format_type = request.data.get('format')
            thumbnail = request.FILES.get('thumbnail')
            
            # Content types validation (1-3 required)
            content_type_ids = request.data.getlist('content_types')
            if not content_type_ids:
                return Response({'message': 'At least one content type is required.'}, status=status.HTTP_400_BAD_REQUEST)
            if len(content_type_ids) > 3:
                return Response({'message': 'Maximum of 3 content types allowed.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate library and category
            try:
                library = Library.objects.get(id=library_id)
                category = Category.objects.get(id=category_id, library=library)
            except Library.DoesNotExist:
                return Response({'message': 'Library not found'}, status=status.HTTP_404_NOT_FOUND)
            except Category.DoesNotExist:
                return Response({'message': f"Category with id {category_id} not found in this library"}, status=status.HTTP_404_NOT_FOUND)
            
            # Validate content types
            from ..models import ContentType
            content_types = []
            for ct_id in content_type_ids:
                try:
                    ct = ContentType.objects.get(id=ct_id, is_active=True)
                    content_types.append(ct)
                except ContentType.DoesNotExist:
                    return Response({'message': f"Content type with id {ct_id} not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Create video record
            video = Video.objects.create(
                title=title,
                description=description,
                subject_area=category,
                library=library,
                uploader=request.user,
                storage_reference_id=s3_key,
                storage_url=f"s3://{settings.AWS_STORAGE_BUCKET_NAME}/{s3_key}",
                storage_status='stored',
                duration=duration,
                file_size=file_size,
                format=format_type
            )
            
            # Set content types and thumbnail
            video.content_types.set(content_types)
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
    BACKEND-READY: Unified video listing with optional category filtering.
    MAPPED TO: /api/videos/ and /api/categories/<name>/videos/
    
    Consolidates VideoListAPIView and CategoryVideosAPIView into one endpoint.
    Returns paginated list of videos with optional category filtering.
    
    URL patterns:
    - /api/videos/ - All videos
    - /api/categories/<category_name>/videos/ - Videos in specific category
    
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
        QUERYSET BUILDER: Get videos with optional category filtering.
        
        Category filtering logic:
        1. If category_name in URL kwargs, filter by that category
        2. Handles both subject areas and paletta categories
        3. Decodes URL encoding and converts hyphens to spaces
        4. Returns empty queryset if category not found
        
        Returns:
            QuerySet: Video objects filtered by category (if specified) and common filters
        """
        queryset = Video.objects.all()
        
        # Category filtering (if category_name is provided in URL)
        category_name = self.kwargs.get('category_name')
        if category_name:
            # Decode URL encoding and handle hyphens vs spaces
            decoded_category_name = urllib.parse.unquote(category_name)
            db_category_name = decoded_category_name.replace('-', ' ')
            
            logger.info(f"Category lookup: '{db_category_name}'")
            
            try:
                # Try subject area first, then paletta category
                try:
                    category = Category.objects.get(subject_area__iexact=db_category_name)
                    queryset = queryset.filter(subject_area=category)
                except Category.DoesNotExist:
                    from ..models import PalettaCategory
                    paletta_category = PalettaCategory.objects.get(code__iexact=db_category_name)
                    queryset = queryset.filter(paletta_category=paletta_category)
            except (Category.DoesNotExist, PalettaCategory.DoesNotExist):
                logger.warning(f"Category '{db_category_name}' not found")
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
    BACKEND-READY: Filter videos by content types with advanced matching.
    MAPPED TO: /api/content-type-videos/
    
    Advanced filtering by content type codes or IDs with AND/OR logic.
    Supports both content type codes ('campus_life') and IDs (1, 2, 3).
    
    Query parameters:
    - content_types: List of content type codes (e.g., campus_life, research_innovation)
    - content_type_ids: List of content type IDs (e.g., 1, 3, 5)
    - match_all: Boolean, if true videos must have ALL specified types (default: ANY)
    - search: Filter by title/description
    - sort_by: 'newest', 'oldest', or 'popular'
    """
    serializer_class = VideoSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """
        QUERYSET BUILDER: Filter videos by content types with flexible matching.
        
        Filtering logic:
        1. Get content_types (codes) and content_type_ids from query params
        2. If match_all=true: Videos must have ALL specified content types
        3. If match_all=false: Videos must have ANY of the specified content types
        4. Apply additional common filters (search, sorting)
        
        Returns:
            QuerySet: Videos filtered by content types and other criteria
        """
        queryset = Video.objects.all()
        
        # Content type filtering
        content_types = self.request.query_params.getlist('content_types', [])
        content_type_ids = self.request.query_params.getlist('content_type_ids', [])
        match_all = self.request.query_params.get('match_all', 'false').lower() == 'true'
        
        if content_types or content_type_ids:
            if match_all:
                # Must have ALL specified content types
                for ct_code in content_types:
                    queryset = queryset.filter(content_types__code=ct_code)
                for ct_id in content_type_ids:
                    queryset = queryset.filter(content_types__id=ct_id)
            else:
                # Must have ANY of the specified content types
                if content_types:
                    queryset = queryset.filter(content_types__code__in=content_types)
                if content_type_ids:
                    queryset = queryset.filter(content_types__id__in=content_type_ids)
        
        # Apply common filters
        queryset = self.apply_video_filters(queryset, self.request)
        
        return queryset


# ==============================================================================
# COMPATIBILITY ALIASES (For existing URL patterns)
# ==============================================================================

# These maintain backward compatibility with existing URLs
VideoListAPIView = UnifiedVideoListAPIView
CategoryVideosAPIView = UnifiedVideoListAPIView 