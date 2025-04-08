from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse

from videos.models import Video


class VideoThumbnailAPIView(LoginRequiredMixin, View):
    """
    API view for getting video thumbnail URLs.
    
    This endpoint allows the frontend to retrieve the thumbnail URL for a 
    specific video when displaying it in the collection.
    """
    
    def get(self, request, clip_id, *args, **kwargs):
        """
        Get the thumbnail URL for a video.
        
        Args:
            request: The HTTP request
            clip_id: The ID of the video
            
        Returns:
            JsonResponse: JSON with thumbnail URL data
        """
        try:
            # Get the video object
            video = get_object_or_404(Video, id=clip_id)
            
            # Get the thumbnail URL
            thumbnail_url = None
            if video.thumbnail:
                thumbnail_url = request.build_absolute_uri(video.thumbnail.url)
            
            # Return the thumbnail URL as JSON
            return JsonResponse({
                'success': True,
                'thumbnail_url': thumbnail_url,
                'video_id': video.id,
                'title': video.title
            })
            
        except Exception as e:
            # Return error response
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500) 