from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.http import Http404
import logging
from ..models import Video, VideoTag

logger = logging.getLogger(__name__)

class VideoDetailView(TemplateView):
    """
    View for displaying detailed information about a video/clip.
    """
    template_name = 'video_details.html'
    
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """Serve the video details page."""
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Get context data for the template."""
        context = super().get_context_data(**kwargs)
        
        # Get the video ID from URL parameters
        video_id = self.kwargs.get('video_id')
        if not video_id:
            raise Http404("Video ID is required")
        
        try:
            # Get the video object and pass it to the context
            clip = get_object_or_404(Video, id=video_id)
            context['clip'] = clip
            
            # Increment view count
            clip.views_count += 1
            clip.save(update_fields=['views_count'])
            
            # Get the video's tags through the VideoTag model
            video_tags = VideoTag.objects.filter(video=clip).select_related('tag')
            
            # Create tag objects that are template-friendly
            tags = []
            for vt in video_tags:
                tags.append({
                    'name': vt.tag.name,
                    'id': vt.tag.id
                })
            context['tags'] = tags
            
            # Format duration for display
            duration_formatted = "Unknown"
            if clip.duration:
                minutes = clip.duration // 60
                seconds = clip.duration % 60
                duration_formatted = f"{minutes}:{seconds:02d}"
            context['duration_formatted'] = duration_formatted
            
            # Get related clips (same category, excluding current)
            context['related_clips'] = Video.objects.filter(
                category=clip.category
            ).exclude(id=clip.id).order_by('-upload_date')[:4]
            
            # CLEAN APPROACH: Library context is handled by middleware
            # Templates will generate slugs on-demand using template tags
            
        except Exception as e:
            logger.error(f"Error retrieving video details: {str(e)}")
            raise Http404("Video not found or unavailable")
        
        return context 