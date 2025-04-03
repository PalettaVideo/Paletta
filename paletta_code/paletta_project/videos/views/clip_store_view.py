from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Count, Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ..models import Category, Tag, Video, VideoTag
from ..serializers import CategorySerializer, VideoSerializer
import urllib.parse
import logging

logger = logging.getLogger(__name__)

class ClipStoreView(TemplateView):
    """View for the clip store page showing all videos."""
    template_name = 'inside_category.html'
    paginate_by = 12
    
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """Serve the clip store page with initial categories and tags."""
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Get context data for the template."""
        context = super().get_context_data(**kwargs)
        
        # Get all categories for the sidebar
        categories = Category.objects.all().order_by('name')
        context['categories'] = categories
        
        # Get popular tags for filtering - annotate with video count and order by that count
        context['popular_tags'] = Tag.objects.annotate(video_count=Count('videotag')).order_by('-video_count')[:20]
        
        # Get initial filter values from query params
        context['category_filter'] = self.request.GET.get('category', 'all')
        context['search_query'] = self.request.GET.get('search', '')
        context['sort_by'] = self.request.GET.get('sort_by', 'newest')
        
        # Get filter parameters
        search_query = self.request.GET.get('search', '')
        tags = self.request.GET.getlist('tags', [])
        sort_by = self.request.GET.get('sort_by', 'newest')
        page = self.request.GET.get('page', 1)
        
        # Fetch videos with filters
        videos_queryset = self.get_videos_queryset(
            category_filter='all',
            search_query=search_query,
            tags=tags,
            sort_by=sort_by
        )
        
        # Paginate results
        paginator = Paginator(videos_queryset, self.paginate_by)
        try:
            videos_page = paginator.page(page)
        except PageNotAnInteger:
            videos_page = paginator.page(1)
        except EmptyPage:
            videos_page = paginator.page(paginator.num_pages)
            
        # Add pagination info to context
        context['videos'] = videos_page.object_list
        context['page_obj'] = videos_page
        context['is_paginated'] = videos_page.has_other_pages()
        context['paginator'] = paginator
        
        return context
    
    def get_videos_queryset(self, category_filter=None, search_query=None, tags=None, sort_by=None):
        """
        Get videos with filters applied.
        
        Args:
            category_filter: Category name or 'all'
            search_query: Search term for title/description
            tags: List of tag names
            sort_by: Sorting option ('newest', 'oldest', 'popular')
            
        Returns:
            QuerySet of Video objects
        """
        # Start with all videos (including unpublished ones for development)
        queryset = Video.objects.all()
        
        # Apply category filter if not 'all'
        if category_filter and category_filter.lower() != 'all':
            queryset = queryset.filter(category__name__iexact=category_filter)
        
        # Apply search filter
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # Apply tag filters
        if tags:
            for tag in tags:
                queryset = queryset.filter(
                    videotag__tag__name__iexact=tag
                )
        
        # Apply sorting
        if sort_by == 'oldest':
            queryset = queryset.order_by('upload_date')
        elif sort_by == 'popular':
            queryset = queryset.order_by('-views_count')
        else:  # Default to 'newest'
            queryset = queryset.order_by('-upload_date')
        
        return queryset.distinct()

class CategoryClipView(ClipStoreView):
    """View for the clip store page showing videos from a specific category."""
    template_name = 'inside_category.html'
    
    def get_context_data(self, **kwargs):
        """Get context data for the template."""
        context = super().get_context_data(**kwargs)
        
        # Get the category name from the URL
        category_name = self.kwargs.get('category', 'all')
        
        # Properly decode the URL-encoded category name
        try:
            decoded_name = urllib.parse.unquote(category_name)
            logger.info(f"Category URL parameter: '{category_name}', decoded: '{decoded_name}'")
        except Exception as e:
            logger.error(f"Error decoding category name: {str(e)}")
            decoded_name = category_name
        
        # Use the decoded name for filtering and display
        context['category_filter'] = decoded_name
        
        # Look up the category in the database if not 'all'
        if decoded_name and decoded_name.lower() != 'all':
            try:
                # Find the category using case-insensitive match
                category = Category.objects.get(name__iexact=decoded_name)
                logger.info(f"Found category: {category.name} (ID: {category.id})")
                
                # Add the category object to context
                context['current_category'] = category
                
                # Add image URLs directly to context
                if category.image:
                    context['category_image_url'] = category.image.url
                
            except Category.DoesNotExist:
                # Category not found
                logger.warning(f"Category not found: '{decoded_name}'")
                context['category_not_found'] = True
                context['attempted_category_name'] = decoded_name
                return context
        
        # Override videos in context with category-filtered videos
        # Get filter parameters
        search_query = self.request.GET.get('search', '')
        tags = self.request.GET.getlist('tags', [])
        sort_by = self.request.GET.get('sort_by', 'newest')
        page = self.request.GET.get('page', 1)
        
        # Fetch videos with category filter
        videos_queryset = self.get_videos_queryset(
            category_filter=decoded_name,
            search_query=search_query,
            tags=tags,
            sort_by=sort_by
        )
        
        # Paginate results
        paginator = Paginator(videos_queryset, self.paginate_by)
        try:
            videos_page = paginator.page(page)
        except PageNotAnInteger:
            videos_page = paginator.page(1)
        except EmptyPage:
            videos_page = paginator.page(paginator.num_pages)
            
        # Add pagination info to context
        context['videos'] = videos_page.object_list
        context['page_obj'] = videos_page
        context['is_paginated'] = videos_page.has_other_pages()
        context['paginator'] = paginator
        
        return context 