from django.views.generic import TemplateView, FormView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views import View
from django.contrib import messages
from ..models import Video, Tag
from django import forms
import os
import subprocess
import json
from ..tasks import upload_video_to_storage
from ..services import VideoLogService
import tempfile
import mimetypes
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

class VideoUploadForm(forms.ModelForm):
    """Form for uploading videos with tags."""
    tags = forms.CharField(required=False, help_text="Comma separated tags")
    
    class Meta:
        model = Video
        fields = ['title', 'description', 'category', 'video_file', 'thumbnail', 'is_published']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        self.library = kwargs.pop('library', None)
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = "Select a category"
        
        # Filter categories by library if library is provided
        if self.library:
            self.fields['category'].queryset = self.fields['category'].queryset.filter(library=self.library)
            
        self.fields['video_file'].required = True
        
    def clean_video_file(self):
        """Validate the video file size."""
        video_file = self.cleaned_data.get('video_file')
        if video_file:
            # Check file size (limit to 5GB)
            max_size = 5 * 1024 * 1024 * 1024  # 5GB in bytes
            if video_file.size > max_size:
                raise forms.ValidationError(f"File size exceeds 5GB. Current size: {video_file.size / (1024 * 1024 * 1024):.2f}GB")
        return video_file

def extract_video_metadata(file_path):
    """
    Extract basic metadata from a video file using ffmpeg/ffprobe.
    Returns a dictionary with metadata information needed for storage.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    metadata = {
        'duration': None,
        'format': None,
        'file_size': None
    }
    
    # Check if file exists
    if not os.path.exists(file_path):
        logger.error(f"File does not exist at path: {file_path}")
        # Try to normalize the path (important for Windows)
        normalized_path = os.path.normpath(file_path)
        logger.info(f"Trying normalized path: {normalized_path}")
        if normalized_path != file_path and os.path.exists(normalized_path):
            logger.info(f"File found at normalized path")
            file_path = normalized_path
        else:
            # Still not found, raise an error with detailed information
            raise FileNotFoundError(f"Video file not found at: {file_path}. Please check file permissions and path.")
    
    # Get file size
    try:
        metadata['file_size'] = os.path.getsize(file_path)
        # Convert to human-readable format
        if metadata['file_size'] < 1024 * 1024:  # Less than 1MB
            metadata['file_size_display'] = f"{metadata['file_size'] / 1024:.1f} KB"
        else:  # MB or GB
            size_mb = metadata['file_size'] / (1024 * 1024)
            if size_mb < 1024:
                metadata['file_size_display'] = f"{size_mb:.1f} MB"
            else:
                metadata['file_size_display'] = f"{size_mb / 1024:.2f} GB"
    except (OSError, IOError) as e:
        logger.error(f"Error getting file size: {e}")
    
    # Get file format from extension
    try:
        file_extension = os.path.splitext(file_path)[1]
        if file_extension:
            metadata['format'] = file_extension.strip('.').upper()
            
        # Use mimetype as fallback
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            metadata['mime_type'] = mime_type
    except Exception as e:
        logger.error(f"Error getting file format: {e}")
    
    # Extract duration using ffprobe
    try:
        # Try to import ffmpeg-python
        try:
            import ffmpeg
            
            # Get video info using ffprobe
            probe = ffmpeg.probe(file_path)
            
            # Extract duration from video stream or format
            if 'format' in probe and 'duration' in probe['format']:
                duration_seconds = float(probe['format']['duration'])
                hours = int(duration_seconds // 3600)
                minutes = int((duration_seconds % 3600) // 60)
                seconds = int(duration_seconds % 60)
                
                if hours > 0:
                    metadata['duration'] = f"{hours}:{minutes:02d}:{seconds:02d}"
                else:
                    metadata['duration'] = f"{minutes}:{seconds:02d}"
                metadata['duration_seconds'] = duration_seconds
                
                # Extract additional metadata if available
                if 'bit_rate' in probe['format']:
                    metadata['bit_rate'] = probe['format']['bit_rate']
                
                # Get video stream info
                video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
                if video_stream:
                    if 'width' in video_stream and 'height' in video_stream:
                        metadata['resolution'] = f"{video_stream['width']}x{video_stream['height']}"
                    if 'codec_name' in video_stream:
                        metadata['codec'] = video_stream['codec_name']
            
        except ImportError:
            logger.error("ffmpeg-python package is not installed. Please install it with: pip install ffmpeg-python")
            raise RuntimeError("ffmpeg-python package is required but not installed")
            
        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if hasattr(e, 'stderr') else str(e)
            logger.error(f"ffmpeg error: {error_message}")
            if "No such file or directory" in str(e) or "not found" in str(e):
                logger.error("ffmpeg/ffprobe is not installed or not in PATH. Please install ffmpeg on your system.")
                raise RuntimeError("ffmpeg/ffprobe is required but not installed on the system")
            raise
            
    except Exception as e:
        logger.error(f"Error extracting duration: {e}")
        # Don't silently fail - raise the exception to make it clear what's missing
        raise
    
    return metadata

class UploadView(FormView):
    """View for the video upload page."""
    template_name = 'upload.html'
    form_class = VideoUploadForm
    success_url = reverse_lazy('upload_history')
    
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """Serve the upload page."""
        return super().get(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        """Pass the current library to the form."""
        kwargs = super().get_form_kwargs()
        
        # Get the current library from session or default to Paletta
        library_id = self.request.session.get('current_library_id')
        if library_id:
            from libraries.models import Library
            try:
                library = Library.objects.get(id=library_id)
                kwargs['library'] = library
            except Library.DoesNotExist:
                # Default to Paletta library if not found
                try:
                    library = Library.objects.get(name='Paletta')
                    kwargs['library'] = library
                except Library.DoesNotExist:
                    pass
        else:
            # Default to Paletta library
            from libraries.models import Library
            try:
                library = Library.objects.get(name='Paletta')
                kwargs['library'] = library
            except Library.DoesNotExist:
                pass
        
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Add the current library to the context."""
        context = super().get_context_data(**kwargs)
        
        # Get the current library from session or default to Paletta
        library_id = self.request.session.get('current_library_id')
        if library_id:
            from libraries.models import Library
            try:
                library = Library.objects.get(id=library_id)
                context['current_library'] = library
            except Library.DoesNotExist:
                # Default to Paletta library if not found
                try:
                    library = Library.objects.get(name='Paletta')
                    context['current_library'] = library
                except Library.DoesNotExist:
                    pass
        else:
            # Default to Paletta library
            from libraries.models import Library
            try:
                library = Library.objects.get(name='Paletta')
                context['current_library'] = library
            except Library.DoesNotExist:
                pass
        
        return context
    
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        """Handle the video upload."""
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
    
    def form_valid(self, form):
        """Process the valid form data and create a video record."""
        try:
            # Create video object but don't save to DB yet
            video = form.save(commit=False)
            video.uploader = self.request.user
            video.storage_status = 'pending'  # Set initial storage status
            
            # Set the library from the form
            if form.library:
                video.library = form.library
            else:
                # If no library in form, try to get from session or default to Paletta
                library_id = self.request.session.get('current_library_id')
                if library_id:
                    from libraries.models import Library
                    try:
                        library = Library.objects.get(id=library_id)
                        video.library = library
                    except Library.DoesNotExist:
                        # Default to Paletta library if not found
                        try:
                            library = Library.objects.get(name='Paletta')
                            video.library = library
                        except Library.DoesNotExist:
                            raise ValueError("No library found for video upload")
                else:
                    # Default to Paletta library
                    from libraries.models import Library
                    try:
                        library = Library.objects.get(name='Paletta')
                        video.library = library
                    except Library.DoesNotExist:
                        raise ValueError("Paletta library not found")
            
            # Save to get an ID for the video
            video.save()
            
            # Process tags (if any)
            tags_text = form.cleaned_data.get('tags', '')
            if tags_text:
                tag_names = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    video.tags.add(tag)
            
            # Extract video metadata
            if video.video_file:
                logger = logging.getLogger(__name__)
                logger.info(f"Extracting metadata from: {video.video_file.path}")
                try:
                    if hasattr(video.video_file, 'path') and video.video_file.path:
                        # Check that file exists
                        if os.path.exists(video.video_file.path):
                            metadata = extract_video_metadata(video.video_file.path)
                            
                            # Update video model with metadata
                            if metadata['file_size']:
                                video.file_size = metadata['file_size']
                            
                            if metadata.get('duration_seconds'):
                                video.duration = int(metadata['duration_seconds'])
                            
                            if metadata.get('format'):
                                video.format = metadata['format']
                            
                            if metadata.get('mime_type'):
                                video.mime_type = metadata['mime_type']
                        else:
                            logger.error(f"File does not exist for metadata extraction: {video.video_file.path}")
                    else:
                        logger.error("Video file has no path attribute")
                except FileNotFoundError as e:
                    logger.error(f"File not found error during metadata extraction: {str(e)}")
                except Exception as e:
                    logger.error(f"Error extracting video metadata: {str(e)}")
                
            # Save again with the updated metadata
            video.save()
            
            # Log the upload
            VideoLogService.log_upload(video, self.request.user, self.request)
            
            # Queue the video for upload to AWS S3 storage
            upload_video_to_storage.delay(video.id)
            
            # Add success message
            messages.success(self.request, f"Video '{video.title}' uploaded successfully and queued for AWS S3 storage.")
            
            return super().form_valid(form)
            
        except Exception as e:
            # Log the error and show error message
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in form_valid: {e}")
            messages.error(self.request, f"Error uploading video: {str(e)}")
            return self.form_invalid(form)

@method_decorator(csrf_exempt, name='dispatch')
class VideoMetadataAPIView(View):
    """API view for extracting metadata from video files without saving them."""
    
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        """Extract metadata from an uploaded video file."""
        try:
            # Check if video file is in the request
            if 'video_file' not in request.FILES:
                return JsonResponse({
                    'success': False,
                    'message': 'No video file provided'
                }, status=400)
                
            video_file = request.FILES['video_file']
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(video_file.name)[1]) as temp_file:
                # Write uploaded file to temporary file
                for chunk in video_file.chunks():
                    temp_file.write(chunk)
                
                temp_path = temp_file.name
            
            # Extract metadata from the temporary file
            try:
                metadata = extract_video_metadata(temp_path)
                
                # Return metadata as JSON
                return JsonResponse({
                    'success': True,
                    'metadata': metadata
                })
            except FileNotFoundError as e:
                return JsonResponse({
                    'success': False,
                    'message': f'File not found error: {str(e)}',
                    'error_type': 'file_not_found'
                }, status=500)
            except RuntimeError as e:
                # Handle specific dependency errors
                if "ffmpeg" in str(e).lower() and ("not installed" in str(e).lower() or "not found" in str(e).lower()):
                    return JsonResponse({
                        'success': False,
                        'message': 'Server configuration error: ffmpeg is not installed. Please contact the administrator.',
                        'error_type': 'dependency_missing',
                        'error_details': str(e)
                    }, status=500)
                else:
                    return JsonResponse({
                        'success': False,
                        'message': f'Runtime error: {str(e)}',
                        'error_type': 'runtime_error'
                    }, status=500)
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_path)
                except (OSError, IOError) as e:
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to remove temporary file: {str(e)}")
                    
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in VideoMetadataAPIView.post: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Error extracting metadata: {str(e)}'
            }, status=500)

class UploadHistoryView(TemplateView):
    """View for the upload history page."""
    template_name = 'upload_history.html'
    
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """Serve the upload history page with the user's videos."""
        context = self.get_context_data(**kwargs)
        context['videos'] = Video.objects.filter(uploader=request.user).order_by('-upload_date')
        return self.render_to_response(context)

class VideoAPIUploadView(View):
    """API view for handling video uploads via AJAX."""
    
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        """Handle the video upload via API."""
        logger = logging.getLogger(__name__)
        logger.info("VideoAPIUploadView.post called")
        
        try:
            # Extract data from request
            title = request.POST.get('title')
            description = request.POST.get('description')
            category_id = request.POST.get('category')
            tags_text = request.POST.get('tags', '')
            is_published = request.POST.get('is_published', 'true').lower() == 'true'
            
            # Log the received data
            logger.info(f"Upload request data: title={title}, category_id={category_id}, tags={tags_text}")
            
            # Check for files
            if 'video_file' not in request.FILES:
                logger.warning("Missing video file in upload request")
                return JsonResponse({
                    'success': False,
                    'message': 'Missing video file'
                }, status=400)
                
            video_file = request.FILES.get('video_file')
            thumbnail = request.FILES.get('thumbnail')
            
            # Log file info
            logger.info(f"Received video file: {video_file.name}, size: {video_file.size}, "
                         f"content type: {video_file.content_type}")
            if thumbnail:
                logger.info(f"Received thumbnail: {thumbnail.name}, size: {thumbnail.size}")
            
            # Validate required fields
            if not all([title, category_id, video_file]):
                missing = []
                if not title: missing.append('title')
                if not category_id: missing.append('category')
                if not video_file: missing.append('video_file')
                
                logger.warning(f"Missing required fields: {', '.join(missing)}")
                return JsonResponse({
                    'success': False,
                    'message': f"Missing required fields: {', '.join(missing)}"
                }, status=400)
            
            # Validate file size (limit to 5GB)
            max_size = 5 * 1024 * 1024 * 1024  # 5GB in bytes
            if video_file.size > max_size:
                logger.warning(f"File size exceeds limit: {video_file.size} > {max_size}")
                return JsonResponse({
                    'success': False,
                    'message': f"File size exceeds 5GB. Current size: {video_file.size / (1024 * 1024 * 1024):.2f}GB"
                }, status=400)
            
            # Create video object
            video = Video(
                title=title,
                description=description,
                category_id=category_id,
                uploader=request.user,
                video_file=video_file,
                thumbnail=thumbnail,
                is_published=is_published,
                storage_status='pending'  # Set initial storage status
            )
            
            # Get library from session or default to Paletta
            library_id = request.session.get('current_library_id')
            if library_id:
                from libraries.models import Library
                try:
                    library = Library.objects.get(id=library_id)
                    video.library = library
                    logger.info(f"Using library from session: {library.name} (ID: {library.id})")
                except Library.DoesNotExist:
                    # Default to Paletta library if not found
                    try:
                        library = Library.objects.get(name='Paletta')
                        video.library = library
                        logger.info(f"Session library not found, using Paletta: {library.id}")
                    except Library.DoesNotExist:
                        logger.error("No library found for video upload")
                        return JsonResponse({
                            'success': False,
                            'message': 'No library found for video upload'
                        }, status=500)
            else:
                # Default to Paletta library
                from libraries.models import Library
                try:
                    library = Library.objects.get(name='Paletta')
                    video.library = library
                    logger.info(f"No library in session, using Paletta: {library.id}")
                except Library.DoesNotExist:
                    logger.error("Paletta library not found")
                    return JsonResponse({
                        'success': False,
                        'message': 'Paletta library not found'
                    }, status=500)
            
            # Save to get an ID
            video.save()
            logger.info(f"Created video record with ID: {video.id}")
            
            # Process tags
            if tags_text:
                tag_names = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
                logger.info(f"Processing tags: {tag_names}")
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    video.tags.add(tag)
            
            # Extract metadata - with improved error handling
            metadata = {}
            try:
                if hasattr(video.video_file, 'path') and video.video_file.path and os.path.exists(video.video_file.path):
                    logger.info(f"Extracting metadata from: {video.video_file.path}")
                    metadata = extract_video_metadata(video.video_file.path)
                    
                    # Update video model with metadata
                    if metadata.get('file_size'):
                        video.file_size = metadata['file_size']
                    
                    if metadata.get('duration_seconds'):
                        video.duration = int(metadata['duration_seconds'])
                    
                    if metadata.get('format'):
                        video.format = metadata['format']
                    
                    if metadata.get('mime_type'):
                        video.mime_type = metadata['mime_type']
                else:
                    logger.warning(f"Cannot extract metadata: File path missing or file doesn't exist")
            except Exception as e:
                logger.error(f"Metadata extraction error: {str(e)}")
                # Continue with the upload even if metadata extraction fails
            
            # Save again with metadata
            video.save()
            logger.info(f"Updated video with metadata: {metadata}")
            
            # Log the upload
            VideoLogService.log_upload(video, request.user, request)
            
            # Queue the video for upload to AWS S3 storage
            upload_video_to_storage.delay(video.id)
            logger.info(f"Queued video {video.id} for storage upload")
            
            return JsonResponse({
                'success': True,
                'video_id': video.id,
                'message': 'Video uploaded successfully and queued for AWS S3 storage'
            })
            
        except Exception as e:
            logger.error(f"Error in VideoAPIUploadView.post: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': f'Error uploading video: {str(e)}'
            }, status=500) 