from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q
from ..models import Video, Category, Tag
from ..serializers import VideoSerializer, CategorySerializer, TagSerializer
import logging
import urllib.parse

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
        queryset = Video.objects.filter(is_published=True)
        
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
        # Get category name from URL and decode URL encoding
        category_name = self.kwargs.get('category_name', '')
        original_name = category_name
        
        # Ensure we properly decode URL-encoded spaces and special characters
        try:
            category_name = urllib.parse.unquote(category_name)
            # Replace hyphens with spaces for database lookup
            db_category_name = category_name.replace('-', ' ')
        except Exception as e:
            print(f"Error decoding category name: {e}")
            db_category_name = category_name
        
        # Debug info for troubleshooting
        print(f"Original category name from URL: '{original_name}'")
        print(f"Decoded category name: '{category_name}'")
        print(f"Database lookup name: '{db_category_name}'")
        
        # List all categories for debugging
        all_categories = list(Category.objects.values_list('name', flat=True))
        print(f"Available categories in database: {all_categories}")
        
        # Try to find the category first to see if it exists
        try:
            category = Category.objects.get(name__iexact=db_category_name)
            print(f"Found category: '{category.name}' (id: {category.id})")
        except Category.DoesNotExist:
            print(f"Error: Category '{db_category_name}' does not exist in database!")
            
        # Continue with the original query
        queryset = Video.objects.filter(
            is_published=True, 
            category__name__iexact=db_category_name
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
        
        # Debug final query count
        result_count = queryset.count()
        print(f"Found {result_count} videos for category '{db_category_name}'")
        
        return queryset.distinct()


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
    
    def post(self, request, format=None):
        try:
            # Get the video file from the request
            video_file = request.FILES.get('video_file')
            
            if not video_file:
                return Response(
                    {"error": "No video file provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Create a new Video object with the provided data
            data = request.data.copy()
            data['video_file'] = video_file
            
            # Handle tags (convert from comma-separated string to list if needed)
            tags_data = data.get('tags', [])
            if isinstance(tags_data, str):
                tags_data = [tag.strip() for tag in tags_data.split(',') if tag.strip()]
                data.pop('tags', None)  # Remove tags from data as we'll handle them separately
            
            # Create and validate the serializer
            serializer = VideoSerializer(data=data, context={'request': request})
            
            if serializer.is_valid():
                # Save the video with the current user as uploader
                video = serializer.save(uploader=request.user)
                
                # Handle tags
                for tag_name in tags_data:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    video.tags.add(tag)
                
                # Return the serialized video data
                return Response(
                    VideoSerializer(video, context={'request': request}).data,
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error in API video upload: {str(e)}")
            return Response(
                {"error": "Failed to upload video", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 