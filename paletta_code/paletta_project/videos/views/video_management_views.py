from django.views.generic import TemplateView, View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
import json
import logging

from ..models import Video, Tag, ContentType
from libraries.models import UserLibraryRole

logger = logging.getLogger(__name__)

class VideoEditView(TemplateView):
    """View for editing a video."""
    template_name = 'edit_video.html'
    
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """Serve the video edit page."""
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)
    
    def get_context_data(self, **kwargs):
        """Get context data for the template."""
        context = super().get_context_data(**kwargs)
        
        video_id = self.kwargs.get('video_id')
        if not video_id:
            context['error'] = "No video ID provided"
            return context
        
        try:
            # Get the video
            video = get_object_or_404(Video, id=video_id)
            
            # Check if the user has permission to edit this video
            if video.uploader != self.request.user:
                # Check if the user has admin/user role for the library
                has_permission = UserLibraryRole.objects.filter(
                    user=self.request.user,
                    library=video.library,
                    role__in=['admin', 'user']
                ).exists()
                
                if not has_permission:
                    context['permission_error'] = True
                    return context
            
            # Format file size for display
            if video.file_size:
                if video.file_size < 1024 * 1024:  # Less than 1MB
                    video.file_size_formatted = f"{video.file_size / 1024:.1f} KB"
                else:  # MB or GB
                    size_mb = video.file_size / (1024 * 1024)
                    if size_mb < 1024:
                        video.file_size_formatted = f"{size_mb:.1f} MB"
                    else:
                        video.file_size_formatted = f"{size_mb / 1024:.2f} GB"
                   
            # Get available content types for the library - Include ALL content types
            content_types = ContentType.objects.filter(
                library=video.library, 
                is_active=True
            ).order_by('subject_area')
            
            # Add to context
            context['video'] = video
            context['content_types'] = content_types
            
        except Video.DoesNotExist:
            context['video_not_found'] = True
        except Exception as e:
            logger.error(f"Error retrieving video for editing: {str(e)}")
            context['error'] = str(e)
        
        return context
    
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        """Handle the video edit form submission."""
        video_id = self.kwargs.get('video_id')
        
        try:
            # Get the video
            video = get_object_or_404(Video, id=video_id)
            
            # Check if the user has permission to edit this video
            if video.uploader != request.user:
                # Check if the user has admin/user role for the library
                has_permission = UserLibraryRole.objects.filter(
                    user=request.user,
                    library=video.library,
                    role__in=['admin', 'user']
                ).exists()
                
                if not has_permission:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'message': 'Permission denied'
                        }, status=403)
                    else:
                        raise PermissionDenied("You don't have permission to edit this video")
            
            # Process form data
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            
            # Handle content type
            content_type_id = request.POST.get('content_type')
            if content_type_id:
                video.content_type = get_object_or_404(ContentType, id=content_type_id)
            
            # Update video fields
            video.title = title
            video.description = description
            
            # Update thumbnail if provided
            if 'thumbnail' in request.FILES:
                # Delete old thumbnail if exists
                if video.thumbnail:
                    video.thumbnail.delete()
                
                video.thumbnail = request.FILES['thumbnail']
            
            # Save changes
            video.save()
            
            # Handle tags
            tags_str = request.POST.get('tags', '')
            if tags_str:
                try:
                    tags_data = json.loads(tags_str)
                    
                    # Clear existing tags
                    video.tags.clear()
                    
                    # Add tags
                    for tag_data in tags_data:
                        tag_id = tag_data.get('id')
                        tag_name = tag_data.get('name')
                        
                        if tag_id:
                            # Use existing tag
                            try:
                                tag = Tag.objects.get(id=tag_id, library=video.library)
                                video.tags.add(tag)
                            except Tag.DoesNotExist:
                                # Tag doesn't exist or belongs to another library
                                continue
                        elif tag_name:
                            # Create new tag or get existing
                            tag, created = Tag.objects.get_or_create(
                                name=tag_name.strip(),
                                library=video.library
                            )
                            video.tags.add(tag)
                            
                            # Log when new tags are created
                            if created:
                                logger.info(f"Edit video: Created new tag '{tag_name}' in library '{video.library.name}'")
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON for tags_list: {tags_str}")
            
            # Return success response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Video updated successfully',
                    'redirect_url': f'/videos/my-videos/'
                })
            else:
                return redirect('my_videos')
            
        except Video.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Video not found'
                }, status=404)
            else:
                raise Http404("Video not found")
        except Exception as e:
            logger.error(f"Error updating video: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                }, status=500)
            else:
                return self.render_to_response(self.get_context_data(
                    error=str(e),
                    **kwargs
                ))

@method_decorator(login_required, name='dispatch')
class VideoDeleteView(View):
    """View for deleting a video."""
    
    @method_decorator(require_POST)
    def post(self, request, video_id):
        """Handle the video deletion."""
        try:
            # Get the video
            video = get_object_or_404(Video, id=video_id)
            
            # Check if the user has permission to delete this video
            # Only the video uploader can delete videos from my videos
            if video.uploader != request.user:
                return JsonResponse({
                    'success': False,
                    'message': 'Only the video uploader can delete this video'
                }, status=403)
            
            # Store video details for logging
            video_title = video.title
            video_uploader = video.uploader.username
            
            # Delete the video (this should call our custom delete method that removes files)
            video.delete()
            
            # Log the deletion
            logger.info(f"Video deleted: '{video_title}' (ID: {video_id}) by {video_uploader}")
            
            return JsonResponse({
                'success': True,
                'message': 'Video deleted successfully'
            })
            
        except Video.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Video not found'
            }, status=404)
        except Exception as e:
            logger.error(f"Error deleting video: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=500)

@method_decorator(login_required, name='dispatch')
class TagSuggestionsAPIView(View):
    """API view for getting tag suggestions."""
    
    def get(self, request):
        """Get tag suggestions based on a query."""
        query = request.GET.get('query', '').strip()
        
        if not query or len(query) < 2:
            return JsonResponse({'tags': []})
        
        try:
            # Get the current library from session
            library_id = request.session.get('current_library_id')
            
            # If no library in session, use all tags
            tags_queryset = Tag.objects.filter(name__icontains=query)
            
            # If library ID is provided, filter by library
            if library_id:
                from libraries.models import Library
                try:
                    library = Library.objects.get(id=library_id)
                    tags_queryset = tags_queryset.filter(library=library)
                except Library.DoesNotExist:
                    pass
            
            # Limit results
            tags = tags_queryset.values('id', 'name')[:10]
            
            return JsonResponse({'tags': list(tags)})
            
        except Exception as e:
            logger.error(f"Error getting tag suggestions: {str(e)}")
            return JsonResponse({
                'error': str(e),
                'tags': []
            }, status=500) 