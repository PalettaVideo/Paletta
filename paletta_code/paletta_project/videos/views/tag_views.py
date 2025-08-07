from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib import messages
import json
import logging

from ..models import Video, Tag, VideoTag
from libraries.models import Library

@login_required
@require_POST
def assign_tags(request, video_id):
    """
    Assign tags to a video based on POST data.
    Clear existing tags and add new ones.
    """
    video = get_object_or_404(Video, id=video_id)
    
    # Check user permissions (video owner or library admin)
    if video.uploader != request.user:
        # Check if user has admin rights for this library
        from libraries.models import UserLibraryRole
        has_permission = UserLibraryRole.objects.filter(
            user=request.user,
            library=video.library,
            role__in=['admin', 'user']
        ).exists()
        
        if not has_permission:
            messages.error(request, "You don't have permission to modify this video's tags.")
            return redirect('video_detail', video_id=video.id)
    
    # Get the tag IDs from the form
    tag_ids = request.POST.getlist('tags')
    
    # Clear existing tags
    video.tags.clear()
    
    # Add selected tags
    for tag_id in tag_ids:
        try:
            tag = Tag.objects.get(id=tag_id, library=video.library)
            video.tags.add(tag)
        except Tag.DoesNotExist:
            # Skip invalid tags
            continue
    
    messages.success(request, "Tags updated successfully.")
    
    # Redirect back to the video detail page
    return redirect('video_detail', video_id=video.id)

@method_decorator(login_required, name='dispatch')
class TagsAPIView(View):
    """API view for managing tags for a video."""
    
    def get(self, request, video_id):
        """Get all tags for a video."""
        try:
            video = Video.objects.get(id=video_id)
            video_tags = video.tags.all().values('id', 'name')
            
            # Get all available tags for this library
            library_tags = Tag.objects.filter(library=video.library).values('id', 'name')
            
            return JsonResponse({
                'success': True,
                'video_tags': list(video_tags),
                'available_tags': list(library_tags)
            })
        except Video.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Video not found'
            }, status=404)
    
    def post(self, request, video_id):
        """Update tags for a video."""
        try:
            video = Video.objects.get(id=video_id)
            
            # Check permissions
            if video.uploader != request.user:
                from libraries.models import UserLibraryRole
                has_permission = UserLibraryRole.objects.filter(
                    user=request.user,
                    library=video.library,
                    role__in=['admin', 'user']
                ).exists()
                
                if not has_permission:
                    return JsonResponse({
                        'success': False,
                        'message': 'Permission denied'
                    }, status=403)
            
            # Parse the JSON data
            try:
                data = json.loads(request.body)
                tag_ids = data.get('tag_ids', [])
                new_tags = data.get('new_tags', [])  # Allow creating new tags
            except json.JSONDecodeError:
                # Fall back to form data if not JSON
                tag_ids = request.POST.getlist('tag_ids')
                new_tags = request.POST.getlist('new_tags')
            
            # Clear existing tags
            video.tags.clear()
            
            # Add tags by ID
            added_tags = []
            for tag_id in tag_ids:
                try:
                    tag = Tag.objects.get(id=tag_id, library=video.library)
                    video.tags.add(tag)
                    added_tags.append({'id': tag.id, 'name': tag.name})
                except Tag.DoesNotExist:
                    continue
            
            # Add new tags
            for tag_name in new_tags:
                if tag_name.strip():
                    # Make sure to specify the library when creating tags
                    tag, created = Tag.objects.get_or_create(
                        name=tag_name.strip(),
                        library=video.library
                    )
                    video.tags.add(tag)
                    tag_info = {'id': tag.id, 'name': tag.name, 'newly_created': created}
                    added_tags.append(tag_info)
                    
                    # Log when new tags are created
                    if created:
                        logger = logging.getLogger(__name__)
                        logger.info(f"API Tags: Created new tag '{tag_name}' in library '{video.library.name}'")
            
            return JsonResponse({
                'success': True,
                'message': 'Tags updated successfully',
                'tags': added_tags
            })
            
        except Video.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Video not found'
            }, status=404) 