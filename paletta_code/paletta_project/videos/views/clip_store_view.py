from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Count, Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ..models import Category, Tag, Video, VideoTag, PalettaCategory
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
    """Get a category by its slug, handling both PalettaCategory and Category objects."""
    if not library:
        return None
    
    if library.uses_paletta_categories:
        # For Paletta-style libraries, search in PalettaCategory objects
        paletta_categories = PalettaCategory.objects.filter(is_active=True)
        for pc in paletta_categories:
            if get_category_slug(pc.display_name) == slug:
                return pc
    else:
        # For custom libraries, search in Category objects
        categories = Category.objects.filter(library=library, is_active=True)
        for category in categories:
            if get_category_slug(category.display_name) == slug:
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
        
        # Use current library from middleware (this is already set by LibraryContextMiddleware)
        current_library = getattr(self.request, 'current_library', None)
        
        # Ensure library is in context (middleware should have set this, but just in case)
        if current_library:
            context['current_library'] = current_library
        
        # Get all categories for the sidebar - ONLY load library-specific Category objects
        if current_library:
            library_categories = Category.objects.filter(
                library=current_library, 
                is_active=True
            ).order_by('subject_area')
            
            logger.debug(f"Found {library_categories.count()} categories for library {current_library.name}")
            
            # Separate Private category to show it first (same as homepage)
            private_category = None
            other_categories = []
            
            for lc in library_categories:
                cat_data = {
                    'id': lc.id,
                    'name': lc.display_name,
                    'display_name': lc.display_name,
                    'subject_area': lc.subject_area,
                    'type': 'library_category',
                }
                
                logger.debug(f"Category: {lc.display_name} (subject_area: {lc.subject_area})")
                
                if lc.subject_area == 'private':
                    private_category = cat_data
                else:
                    other_categories.append(cat_data)
            
            # Add Private category first (pinned), then other categories
            categories = []
            if private_category:
                categories.append(private_category)
                logger.debug("Added Private category to sidebar")
            categories.extend(other_categories)
            
            context['categories'] = categories
            logger.debug(f"Total categories in context: {len(categories)}")
        else:
            context['categories'] = []
            
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

        # Filter private videos based on user permissions
        if user.is_authenticated:
            # For authenticated users, exclude private videos unless they're the library owner
            if library:
                # UNIFIED APPROACH: Only check subject_area for private videos
                private_videos_q = Q(subject_area__subject_area='private') & ~Q(library__owner=user)
                queryset = queryset.exclude(private_videos_q)
        else:
            # For anonymous users, exclude ALL private videos
            queryset = queryset.exclude(Q(subject_area__subject_area='private'))
        
        # Filter by library if specified
        if library:
            queryset = queryset.filter(library=library)
        
        # Apply category filter if not 'all'
        if category_filter and category_filter.lower() != 'all':
            # UNIFIED APPROACH: All videos now use subject_area field
            # Whether it's Paletta-style or custom, we filter by subject_area (Category objects)
            try:
                # Find the Category that matches the display_name
                matching_category = None
                for cat in Category.objects.filter(library=library, is_active=True):
                    if cat.display_name.lower() == category_filter.lower():
                        matching_category = cat
                        break
                
                if matching_category:
                    queryset = queryset.filter(subject_area=matching_category)
                    logger.debug(f"Filtering videos by subject_area: {matching_category.display_name} (ID: {matching_category.id})")
                else:
                    # If no matching category found, return empty queryset
                    logger.warning(f"No matching category found for filter '{category_filter}' in library {library.name if library else 'None'}")
                    queryset = queryset.none()
            except Exception as e:
                logger.error(f"Error filtering by category '{category_filter}': {e}")
                queryset = queryset.none()
        
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
        
        # Use current library from middleware (this is already set by LibraryContextMiddleware)
        current_library = getattr(self.request, 'current_library', None)
        category_slug = self.kwargs.get('category_slug')
        
        # Ensure library is in context (middleware should have set this, but just in case)
        if current_library:
            context['current_library'] = current_library
        
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
        
        # Get the category based on the slug
        if category_slug and category_slug != 'clip-store':
            # Get category by slug (handles both PalettaCategory and Category)
            category = get_category_by_slug(category_slug, current_library)
            if category:
                context['current_category'] = category
                context['category_slug'] = category_slug
                
                # Handle display name based on category type
                if hasattr(category, 'display_name'):
                    context['category_filter'] = category.display_name
                else:
                    context['category_filter'] = str(category)
                
                # Add image URLs directly to context (only Category objects have images)
                if hasattr(category, 'image') and category.image:
                    context['category_image_url'] = category.image.url
            else:
                # Category not found
                context['category_not_found'] = True
                context['attempted_category_name'] = category_slug
                logger.warning(f"Category not found for slug: '{category_slug}' in library: {current_library.name if current_library else 'None'}")
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