from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics, parsers
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q
from django.db import IntegrityError
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
# S3 MULTIPART UPLOAD ENDPOINTS (For large file uploads)
# ==============================================================================

class S3MultipartUploadView(APIView):
    """
    Create multipart upload for large files.
    MAPPED TO: /api/s3/create-multipart-upload/
    USED BY: Frontend multipart upload for files > 5MB
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, format=None):
        try:
            bucket = request.data.get('bucket')
            key = request.data.get('key')
            content_type = request.data.get('content_type')
            
            if not all([bucket, key, content_type]):
                return Response(
                    {'error': 'Missing required fields: bucket, key, content_type'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Initialize S3 client
            from ..services import AWSCloudStorageService
            storage_service = AWSCloudStorageService()
            
            if not storage_service.storage_enabled:
                return Response(
                    {'error': 'S3 storage is not enabled'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Create multipart upload
            response = storage_service.s3_client.create_multipart_upload(
                Bucket=bucket,
                Key=key,
                ContentType=content_type,
                ACL='private'
            )
            
            return Response({
                'upload_id': response['UploadId'],
                'key': key,
                'bucket': bucket
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating multipart upload: {str(e)}")
            return Response(
                {'error': 'Failed to create multipart upload'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class S3UploadPartView(APIView):
    """
    Get presigned URL for uploading a part.
    MAPPED TO: /api/s3/get-upload-part-url/
    USED BY: Frontend multipart upload for individual parts
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, format=None):
        try:
            bucket = request.data.get('bucket')
            key = request.data.get('key')
            upload_id = request.data.get('upload_id')
            part_number = request.data.get('part_number')
            
            if not all([bucket, key, upload_id, part_number]):
                return Response(
                    {'error': 'Missing required fields: bucket, key, upload_id, part_number'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Initialize S3 client
            from ..services import AWSCloudStorageService
            storage_service = AWSCloudStorageService()
            
            if not storage_service.storage_enabled:
                return Response(
                    {'error': 'S3 storage is not enabled'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Generate presigned URL for part upload
            presigned_url = storage_service.s3_client.generate_presigned_url(
                'upload_part',
                Params={
                    'Bucket': bucket,
                    'Key': key,
                    'UploadId': upload_id,
                    'PartNumber': part_number
                },
                ExpiresIn=3600  # 1 hour expiry
            )
            
            return Response({
                'presigned_url': presigned_url,
                'part_number': part_number
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating upload part URL: {str(e)}")
            return Response(
                {'error': 'Failed to generate upload part URL'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class S3CompleteMultipartUploadView(APIView):
    """
    Complete multipart upload.
    MAPPED TO: /api/s3/complete-multipart-upload/
    USED BY: Frontend multipart upload completion
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, format=None):
        try:
            bucket = request.data.get('bucket')
            key = request.data.get('key')
            upload_id = request.data.get('upload_id')
            parts = request.data.get('parts', [])
            
            if not all([bucket, key, upload_id]) or not parts:
                return Response(
                    {'error': 'Missing required fields: bucket, key, upload_id, parts'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Initialize S3 client
            from ..services import AWSCloudStorageService
            storage_service = AWSCloudStorageService()
            
            if not storage_service.storage_enabled:
                return Response(
                    {'error': 'S3 storage is not enabled'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Complete multipart upload
            response = storage_service.s3_client.complete_multipart_upload(
                Bucket=bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            
            return Response({
                'location': response.get('Location'),
                'etag': response.get('ETag'),
                'key': key
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error completing multipart upload: {str(e)}")
            return Response(
                {'error': 'Failed to complete multipart upload'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class S3AbortMultipartUploadView(APIView):
    """
    Abort multipart upload.
    MAPPED TO: /api/s3/abort-multipart-upload/
    USED BY: Frontend multipart upload cleanup on failure
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, format=None):
        try:
            bucket = request.data.get('bucket')
            key = request.data.get('key')
            upload_id = request.data.get('upload_id')
            
            if not all([bucket, key, upload_id]):
                return Response(
                    {'error': 'Missing required fields: bucket, key, upload_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Initialize S3 client
            from ..services import AWSCloudStorageService
            storage_service = AWSCloudStorageService()
            
            if not storage_service.storage_enabled:
                return Response(
                    {'error': 'S3 storage is not enabled'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Abort multipart upload
            storage_service.s3_client.abort_multipart_upload(
                Bucket=bucket,
                Key=key,
                UploadId=upload_id
            )
            
            return Response({
                'message': 'Multipart upload aborted successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error aborting multipart upload: {str(e)}")
            return Response(
                {'error': 'Failed to abort multipart upload'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ==============================================================================
# METADATA CREATION ENDPOINT (After S3 upload completes)
# ==============================================================================

class VideoAPIUploadView(APIView):
    """
    Main video upload endpoint for metadata creation.
    MAPPED TO: /api/uploads/
    USED BY: upload.js line 635
    
    Creates video database record after successful S3 upload completes.
    This is the final step in the upload process flow:
    1. Frontend uploads file directly to S3 using presigned URL
    2. Frontend calls this endpoint with S3 key and metadata
    3. This endpoint creates the Video record with storage_status='stored'
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    
    def post(self, request, format=None):
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
            
            # Validation
            if not title or not title.strip():
                return Response({'message': 'Title is required and cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)
            
            if len(title) > 25:
                return Response({'message': 'Title cannot exceed 25 characters.'}, status=status.HTTP_400_BAD_REQUEST)
            
            if duration is not None:
                try:
                    duration = int(duration)
                    if duration < 0:
                        return Response({'message': 'Duration cannot be negative.'}, status=status.HTTP_400_BAD_REQUEST)
                    if duration > 86400:
                        return Response({'message': 'Duration cannot exceed 24 hours (86400 seconds).'}, status=status.HTTP_400_BAD_REQUEST)
                except (ValueError, TypeError):
                    return Response({'message': 'Duration must be a valid integer.'}, status=status.HTTP_400_BAD_REQUEST)
            
            if file_size is not None:
                try:
                    file_size = int(file_size)
                    if file_size < 0:
                        return Response({'message': 'File size cannot be negative.'}, status=status.HTTP_400_BAD_REQUEST)
                    if file_size > 10737418240:
                        return Response({'message': 'File size cannot exceed 10GB.'}, status=status.HTTP_400_BAD_REQUEST)
                except (ValueError, TypeError):
                    return Response({'message': 'File size must be a valid integer.'}, status=status.HTTP_400_BAD_REQUEST)
            
            if not content_type_id:
                return Response({'message': 'Content type is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate library and content type
            try:
                library = Library.objects.get(id=library_id)
            except Library.DoesNotExist:
                return Response({'message': 'Library not found'}, status=status.HTTP_404_NOT_FOUND)
            
            try:
                content_type = ContentType.objects.get(
                    id=content_type_id, 
                    library=library, 
                    is_active=True
                )
            except ContentType.DoesNotExist:
                return Response({
                    'message': f"Content type with id {content_type_id} not found in library '{library.name}' or is inactive"
                }, status=status.HTTP_404_NOT_FOUND)
            
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
                
            # Handle tags with race condition protection
            if tags_str:
                tag_names = [name.strip() for name in tags_str.split(',') if name.strip()]
                for tag_name in tag_names:
                    try:
                        tag = Tag.objects.get(name=tag_name, library=library)
                    except Tag.DoesNotExist:
                        try:
                            tag = Tag.objects.create(name=tag_name, library=library)
                        except IntegrityError:
                            tag = Tag.objects.get(name=tag_name, library=library)
                    
                    VideoTag.objects.get_or_create(video=video, tag=tag)
                    
            serializer = VideoSerializer(video, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Error in VideoAPIUploadView: {e}")
            return Response({'message': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PopularTagsAPIView(APIView):
    """
    Get popular tags for video filtering interface.
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
# VIDEO LISTING ENDPOINTS (Used by frontend)
# ==============================================================================

class UnifiedVideoListAPIView(generics.ListAPIView, VideoFilterMixin):
    """
    Unified video listing with optional content type filtering.
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
    Get single video details with view count increment.
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