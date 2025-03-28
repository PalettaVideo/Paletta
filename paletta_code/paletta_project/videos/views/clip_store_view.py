from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Count
from ..models import Category, Tag, Video
from ..serializers import CategorySerializer
import urllib.parse
import logging

logger = logging.getLogger(__name__)

class ClipStoreView(TemplateView):
    """View for the clip store page showing all videos."""
    template_name = 'inside_category.html'
    
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
        context['popular_tags'] = Tag.objects.annotate(video_count=Count('videos')).order_by('-video_count')[:20]
        
        # Get initial filter values from query params
        context['category_filter'] = self.request.GET.get('category', 'all')
        context['search_query'] = self.request.GET.get('search', '')
        context['sort_by'] = self.request.GET.get('sort_by', 'newest')
        
        return context

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
                if category.banner:
                    context['category_banner_url'] = category.banner.url
                
                if category.image:
                    context['category_image_url'] = category.image.url
                
            except Category.DoesNotExist:
                # Category not found
                logger.warning(f"Category not found: '{decoded_name}'")
                context['category_not_found'] = True
                context['attempted_category_name'] = decoded_name
        
        return context 