from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Count, Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ..models import Category, Tag, Video, VideoTag
from ..serializers import CategorySerializer, VideoSerializer
import urllib.parse
import logging
from django.shortcuts import redirect
from django.urls import reverse

from accounts.views.home_view import get_library_by_slug
from django.utils.text import slugify
from libraries.models import Library

def get_category_slug(category_name):
    """Convert a category name to a URL-friendly slug."""
    return slugify(category_name)

def get_category_by_slug(slug, library=None):
    """Get a category by its slug, optionally filtering by library."""
    if library:
        categories = Category.objects.filter(library=library)
    else:
        categories = Category.objects.all()
        
    for category in categories:
        if get_category_slug(category.name) == slug:
            return category
    return None

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
        
        # Check for library slug in URL or query parameter
        library_slug = self.kwargs.get('library_slug')
        current_library = None
        
        if library_slug:
            # New URL format with library_slug
            current_library = get_library_by_slug(library_slug)
            if current_library:
                context['current_library'] = current_library
        else:
            # Legacy format with library_id
            library_id = self.request.GET.get('library_id')
            if library_id:
                try:
                    current_library = Library.objects.get(id=library_id)
                    context['current_library'] = current_library
                except Library.DoesNotExist:
                    pass
        
        # Get all categories for the sidebar, filtered by library if available
        if current_library:
            categories = Category.objects.filter(library=current_library).order_by('name')
        else:
            categories = Category.objects.all().order_by('name')
            
        context['categories'] = categories
        
        # Get popular tags for filtering - annotate with video count and order by that count
        if current_library:
            # Filter tags by the current library
            context['popular_tags'] = Tag.objects.filter(library=current_library).annotate(
                video_count=Count('videotag')
            ).order_by('-video_count')[:20]
        else:
            context['popular_tags'] = Tag.objects.annotate(
                video_count=Count('videotag')
            ).order_by('-video_count')[:20]
        
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
            sort_by=sort_by,
            library=current_library  # Pass the library for filtering
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
    
    def get_videos_queryset(self, category_filter=None, search_query=None, tags=None, sort_by=None, library=None):
        """
        Get videos with filters applied.
        
        Args:
            category_filter: Category name or 'all'
            search_query: Search term for title/description
            tags: List of tag names
            sort_by: Sorting option ('newest', 'oldest', 'popular')
            library: Library object to filter videos by
            
        Returns:
            QuerySet of Video objects
        """
        # Start with all videos (including unpublished ones for development)
        queryset = Video.objects.all()
        user = self.request.user

        # Exclude videos from 'Private' categories if the user is not the library owner
        if user.is_authenticated:
            private_video_q = Q(category__name='Private') & ~Q(library__owner=user)
            queryset = queryset.exclude(private_video_q)
        else:
            # Exclude all private videos for anonymous users
            queryset = queryset.exclude(category__name='Private')
        
        # Filter by library if specified
        if library:
            queryset = queryset.filter(library=library)
        
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
        
        # Check for new URL format with library_slug and category_slug
        library_slug = self.kwargs.get('library_slug')
        category_slug = self.kwargs.get('category_slug')
        
        # Get the library if specified
        current_library = None
        if library_slug:
            current_library = get_library_by_slug(library_slug)
            if not current_library:
                context['library_not_found'] = True
                context['attempted_library_slug'] = library_slug
                return context
            
            # Add library info to context
            context['current_library'] = current_library
        else:
            # Legacy format - check for library_id parameter
            library_id = self.request.GET.get('library_id')
            if library_id:
                try:
                    current_library = Library.objects.get(id=library_id)
                    context['current_library'] = current_library
                except Library.DoesNotExist:
                    pass
        
        # Special case for "clip-store" slug - this represents all videos
        if category_slug == 'clip-store':
            context['category_filter'] = 'all'
            context['is_clip_store'] = True  # Flag to indicate we're in the all videos view
            logger.info(f"Rendering clip-store (all videos) for library: {current_library.name if current_library else 'None'}")
            
            # Get filter parameters
            search_query = self.request.GET.get('search', '')
            tags = self.request.GET.getlist('tags', [])
            sort_by = self.request.GET.get('sort_by', 'newest')
            page = self.request.GET.get('page', 1)
            
            # Fetch videos with filters but no category filter
            videos_queryset = self.get_videos_queryset(
                category_filter='all',
                search_query=search_query,
                tags=tags,
                sort_by=sort_by,
                library=current_library  # Pass the library for filtering
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
        
        # Get the category based on either the slug or the URL parameter
        if category_slug and category_slug != 'clip-store':
            # New format - get category by slug
            category = get_category_by_slug(category_slug, current_library)
            if category:
                context['current_category'] = category
                context['category_slug'] = category_slug
                context['category_filter'] = category.name
                
                # Add image URLs directly to context
                if category.image:
                    context['category_image_url'] = category.image.url
            else:
                # Category not found
                context['category_not_found'] = True
                context['attempted_category_name'] = category_slug
                return context
        else:
            # Legacy format - get category from URL parameter
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
                    filters = {'name__iexact': decoded_name}
                    if current_library:
                        filters['library'] = current_library
                        
                    category = Category.objects.get(**filters)
                    logger.info(f"Found category: {category.name} (ID: {category.id})")
                    
                    # Add the category object to context
                    context['current_category'] = category
                    context['category_slug'] = get_category_slug(category.name)
                    
                    # Add image URLs directly to context
                    if category.image:
                        context['category_image_url'] = category.image.url
                    
                except Category.DoesNotExist:
                    # Category not found
                    logger.warning(f"Category not found: '{decoded_name}'")
                    context['category_not_found'] = True
                    context['attempted_category_name'] = decoded_name
                    return context
        
        # Get the category filter name for the query
        category_filter = context.get('category_filter', 'all')
        
        # Override videos in context with category-filtered videos
        # Get filter parameters
        search_query = self.request.GET.get('search', '')
        tags = self.request.GET.getlist('tags', [])
        sort_by = self.request.GET.get('sort_by', 'newest')
        page = self.request.GET.get('page', 1)
        
        # Fetch videos with category filter
        videos_queryset = self.get_videos_queryset(
            category_filter=category_filter,
            search_query=search_query,
            tags=tags,
            sort_by=sort_by,
            library=current_library  # Pass the library for filtering
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