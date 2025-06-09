from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics, parsers
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q
from ..models import Video, Category, Tag, VideoTag
from ..serializers import VideoSerializer, CategorySerializer, TagSerializer
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


class VideoListAPIView(generics.ListAPIView):
    """
    API view to list videos with filtering and pagination.
    
    This endpoint supports the following query parameters:
    - search: Search in video titles and descriptions
    - category: Filter by category ID
    - tags: Filter by tag names (can be used multiple times)
    - sort_by: Sort videos by 'newest', 'oldest', 'popular', 'az', or 'za'
    - page: Page number for pagination
    - page_size: Number of items per page (max 100)
    """
    serializer_class = VideoSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Video.objects.all()
        
        # Apply search filter
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # Apply category filter
        category = self.request.query_params.get('category', None)
        if category and category.lower() != 'all':
            queryset = queryset.filter(category__name__iexact=category)
        
        # Apply tags filter
        tags = self.request.query_params.getlist('tags', [])
        if tags:
            # Filter videos that have all the specified tags
            for tag in tags:
                queryset = queryset.filter(tags__name__iexact=tag)
        
        # Apply sorting
        sort_by = self.request.query_params.get('sort_by', 'newest')
        
        if sort_by == 'newest':
            queryset = queryset.order_by('-upload_date')
        elif sort_by == 'oldest':
            queryset = queryset.order_by('upload_date')
        elif sort_by == 'popular':
            queryset = queryset.order_by('-views_count')
        elif sort_by == 'az':
            queryset = queryset.order_by('title')
        elif sort_by == 'za':
            queryset = queryset.order_by('-title')
        else:
            queryset = queryset.order_by('-upload_date')  # Default to newest
        
        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        """Override list method to ensure empty results return a valid empty array"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Check if queryset is empty and handle specifically
        if not queryset.exists():
            logger.info("Returning empty results array for videos request")
            return Response({"count": 0, "results": []})
            
        # Continue with standard pagination if there are results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class VideoDetailAPIView(generics.RetrieveAPIView):
    """
    API view to retrieve details for a specific video.
    """
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [permissions.AllowAny]
    lookup_url_kwarg = 'video_id'
    
    def retrieve(self, request, *args, **kwargs):
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


class CategoryVideosAPIView(generics.ListAPIView):
    """
    API view to list videos for a specific category.
    
    This endpoint supports the same query parameters as VideoListAPIView
    but filters videos by the category name specified in the URL path.
    """
    serializer_class = VideoSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        # Get category name from URL and decode it properly
        encoded_category_name = self.kwargs.get('category_name', '')
        
        # First, decode any URL encoding
        decoded_category_name = urllib.parse.unquote(encoded_category_name)
        
        # For consistent database lookup, use spaces instead of hyphens
        # This is needed regardless of whether the URL contains hyphens or %20
        db_category_name = decoded_category_name.replace('-', ' ')
        
        logger.info(f"Category lookup: encoded='{encoded_category_name}', decoded='{decoded_category_name}', db_lookup='{db_category_name}'")
        
        # Try to find the category first to confirm it exists
        try:
            category = Category.objects.get(name__iexact=db_category_name)
            logger.info(f"Found category: '{category.name}' (id: {category.id})")
        except Category.DoesNotExist:
            logger.warning(f"Category '{db_category_name}' does not exist in database")
            return Video.objects.none()  # Return empty queryset if category doesn't exist
        
        # Continue with queryset filtering using the found category
        queryset = Video.objects.filter(
            category=category
        )
        
        # Apply search filter
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # Apply tags filter
        tags = self.request.query_params.getlist('tags', [])
        if tags:
            for tag in tags:
                queryset = queryset.filter(tags__name__iexact=tag)
        
        # Apply sorting
        sort_by = self.request.query_params.get('sort_by', 'newest')
        
        if sort_by == 'newest':
            queryset = queryset.order_by('-upload_date')
        elif sort_by == 'oldest':
            queryset = queryset.order_by('upload_date')
        elif sort_by == 'popular':
            queryset = queryset.order_by('-views_count')
        elif sort_by == 'az':
            queryset = queryset.order_by('title')
        elif sort_by == 'za':
            queryset = queryset.order_by('-title')
        else:
            queryset = queryset.order_by('-upload_date')  # Default to newest
        
        # Log final query count
        result_count = queryset.count()
        logger.info(f"Found {result_count} videos for category '{db_category_name}'")
        
        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        """Override list method to ensure empty results return a valid empty array"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Check if queryset is empty and handle specifically
        if not queryset.exists():
            logger.info("Returning empty results array for category videos request")
            return Response({"count": 0, "results": []})
            
        # Continue with standard pagination if there are results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PopularTagsAPIView(APIView):
    """
    API view to retrieve the most popular tags based on video count.
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, format=None):
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


class VideoMetadataAPIView(APIView):
    """
    API view to extract metadata from a video file.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, format=None):
        try:
            # The file should be in request.FILES
            video_file = request.FILES.get('video_file')
            
            if not video_file:
                return Response(
                    {"error": "No video file provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # In a real implementation, you would:
            # 1. Get file details (size, duration, etc.)
            # 2. Extract metadata from the video
            # 3. Return the metadata
            # For simplicity, we'll just return basic file information
            
            metadata = {
                'filename': video_file.name,
                'file_size': video_file.size,
                'content_type': video_file.content_type,
                # Duration would normally be extracted from the video
                'estimated_duration': 0  
            }
            
            return Response(metadata)
            
        except Exception as e:
            logger.error(f"Error extracting video metadata: {str(e)}")
            return Response(
                {"error": "Unable to extract video metadata"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VideoAPIUploadView(APIView):
    """
    API view for direct video uploads.
    
    This endpoint handles video uploads through the API rather than
    the standard form-based upload process.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    
    def post(self, request, format=None):
        s3_key = request.data.get('s3_key')
        if not s3_key:
            return Response({'message': 's3_key is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # Get data from request
            title = request.data.get('title', 'Untitled Video')
            description = request.data.get('description', '')
            category_id = request.data.get('category')
            library_id = request.data.get('library_id')
            tags_str = request.data.get('tags', '')
            duration = request.data.get('duration')
            file_size = request.data.get('file_size')
            format_type = request.data.get('format')
            thumbnail = request.FILES.get('thumbnail')
            
            # Find the library
            try:
                library = Library.objects.get(id=library_id)
            except Library.DoesNotExist:
                return Response({'message': 'Library not found'}, status=status.HTTP_404_NOT_FOUND)

            # Find the category
            try:
                category = Category.objects.get(id=category_id, library=library)
            except Category.DoesNotExist:
                return Response({'message': f"Category with id {category_id} not found in this library"}, status=status.HTTP_404_NOT_FOUND)
            
            # Create the video object
            video = Video.objects.create(
                title=title,
                description=description,
                category=category,
                library=library,
                uploader=request.user,
                storage_reference_id=s3_key,
                storage_url=f"s3://{settings.AWS_STORAGE_BUCKET_NAME}/{s3_key}",
                storage_status='stored',  # Set status to stored, no more processing needed
                duration=duration,
                file_size=file_size,
                format=format_type
            )
            
            # Save the thumbnail if it was provided
            if thumbnail:
                video.thumbnail = thumbnail
                video.save(update_fields=['thumbnail'])
                
                # Handle tags
            if tags_str:
                tag_names = [name.strip() for name in tags_str.split(',') if name.strip()]
                for tag_name in tag_names:
                    tag, _ = Tag.objects.get_or_create(name=tag_name, library=library)
                    VideoTag.objects.create(video=video, tag=tag)
                    
            # --- The Celery task for post-processing is no longer needed ---
            # process_video_from_s3.delay(video.id)

            serializer = VideoSerializer(video, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Error in VideoAPIUploadView: {e}")
            return Response({'message': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 