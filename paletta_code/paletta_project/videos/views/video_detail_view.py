from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.http import Http404
import logging
from ..models import Video, VideoTag
from accounts.views.home_view import get_library_slug

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
            # Get the video object
            clip = get_object_or_404(Video, id=video_id)
            
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
            
            # Format duration for display
            duration_formatted = "Unknown"
            if clip.duration:
                minutes = clip.duration // 60
                seconds = clip.duration % 60
                duration_formatted = f"{minutes}:{seconds:02d}"
            
            # Get related clips (same category, excluding current)
            related_clips = Video.objects.filter(
                category=clip.category,
                is_published=True
            ).exclude(id=clip.id).order_by('-upload_date')[:4]
            
            # Prepare related clips data for the template
            related_clips_data = []
            for related in related_clips:
                related_data = {
                    'id': related.id,
                    'title': related.title,
                    'thumbnail': related.thumbnail.url if related.thumbnail else None
                }
                related_clips_data.append(related_data)
            
            # Add library information to context if available
            if clip.library:
                context['library'] = {
                    'name': clip.library.name,
                    'slug': get_library_slug(clip.library.name)
                }
            
            # Create a clip dictionary with all needed properties
            clip_dict = {
                'id': clip.id,
                'title': clip.title,
                'description': clip.description,
                'upload_date': clip.upload_date,
                'category': clip.category.name,
                'tags': tags,
                'duration': duration_formatted,
                'frame_rate': getattr(clip, 'frame_rate', 'Unknown'),
                'resolution': getattr(clip, 'resolution', 'Unknown'),
                'format': getattr(clip, 'format', 'Unknown'),
                'video_url': clip.video_file.url if clip.video_file else clip.storage_url
            }
            
            # Add a tags.all property to match the template expectations
            class TagList:
                def __init__(self, tags):
                    self.tags = tags
                
                def all(self):
                    return self.tags
            
            clip_dict['tags'] = TagList(tags)
            
            # Add clip data to context
            context['clip'] = clip_dict
            
            # Add related clips to context
            context['related_clips'] = related_clips_data
            
        except Exception as e:
            logger.error(f"Error retrieving video details: {str(e)}")
            raise Http404("Video not found or unavailable")
        
        return context 