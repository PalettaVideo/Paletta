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
from ..services import VideoLogService
import tempfile
import mimetypes
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging


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
            # NOTE: For very large files (e.g., > 5GB), a direct-to-S3 upload architecture
            # is strongly recommended to avoid overwhelming the server's disk and memory.
            # This validation should be paired with a corresponding frontend check.
            max_size = 256 * 1024 * 1024 * 1024  # 256GB in bytes
            if video_file.size > max_size:
                raise forms.ValidationError(f"File size exceeds 256GB. Current size: {video_file.size / (1024 * 1024 * 1024):.2f}GB")
        return video_file

def extract_video_metadata(file_path):
    """
    Extract basic metadata from a video file using ffmpeg/ffprobe.
    Returns a dictionary with metadata information needed for storage.
    If ffmpeg/ffprobe is not available, returns basic file metadata.
    """
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
    
    # Get basic file metadata that doesn't require ffmpeg
    try:
        # Get file size
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
                
        # Get file format from extension
        file_extension = os.path.splitext(file_path)[1]
        if file_extension:
            metadata['format'] = file_extension.strip('.').upper()
            
        # Use mimetype as fallback
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            metadata['mime_type'] = mime_type
    except (OSError, IOError) as e:
        logger.error(f"Error getting basic file metadata: {e}")
    
    # Check if ffprobe/ffmpeg is installed before attempting to use it
    ffprobe_available = False
    try:
        # Try checking for ffprobe directly
        import shutil
        ffprobe_path = shutil.which('ffprobe')
        if ffprobe_path:
            logger.info(f"ffprobe found at: {ffprobe_path}")
            ffprobe_available = True
        else:
            # On Windows, try common installation paths
            if os.name == 'nt':
                possible_paths = [
                    r"C:\ffmpeg\bin\ffprobe.exe",
                    r"C:\Program Files\ffmpeg\bin\ffprobe.exe",
                    r"C:\Program Files (x86)\ffmpeg\bin\ffprobe.exe",
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        logger.info(f"ffprobe found at common location: {path}")
                        ffprobe_available = True
                        break
            
            if not ffprobe_available:
                logger.warning("ffprobe not found in PATH or common locations")
    except Exception as e:
        logger.error(f"Error checking for ffprobe: {e}")
    
    # If ffprobe not available, return basic metadata
    if not ffprobe_available:
        logger.warning("ffprobe not available, using basic metadata only")
        metadata['extraction_method'] = 'basic'
        return metadata
    
    # Try to extract advanced metadata using ffprobe if available
    try:
        # Try to import ffmpeg-python
        try:
            import ffmpeg
            
            # Get video info using ffprobe
            logger.info(f"Attempting to probe file with ffmpeg-python: {file_path}")
            probe = ffmpeg.probe(file_path)
            logger.info(f"Probe successful, got data: {len(str(probe))} bytes")
            
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
                logger.info(f"Extracted duration: {metadata['duration']} ({duration_seconds} seconds)")
                
                # Extract additional metadata if available
                if 'bit_rate' in probe['format']:
                    metadata['bit_rate'] = probe['format']['bit_rate']
                
                # Get video stream info
                video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
                if video_stream:
                    if 'width' in video_stream and 'height' in video_stream:
                        metadata['resolution'] = f"{video_stream['width']}x{video_stream['height']}"
                        logger.info(f"Extracted resolution: {metadata['resolution']}")
                    if 'codec_name' in video_stream:
                        metadata['codec'] = video_stream['codec_name']
                        logger.info(f"Extracted codec: {metadata['codec']}")
            else:
                logger.warning("No duration found in probe data")
                
        except ImportError:
            logger.warning("ffmpeg-python package is not installed. Using basic metadata only.")
            metadata['extraction_method'] = 'basic'
            return metadata
            
        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if hasattr(e, 'stderr') else str(e)
            logger.warning(f"ffmpeg error: {error_message}")
            if "No such file or directory" in str(e) or "not found" in str(e):
                logger.warning("ffmpeg/ffprobe is not installed or not in PATH. Using basic metadata only.")
                metadata['extraction_method'] = 'basic'
                return metadata
            
            # For other ffmpeg errors, log but continue with basic metadata
            logger.error(f"Other ffmpeg error: {error_message}")
            metadata['extraction_method'] = 'basic'
            return metadata
            
    except Exception as e:
        logger.warning(f"Error extracting advanced metadata with ffmpeg: {e}. Using basic metadata only.")
        metadata['extraction_method'] = 'basic'
        return metadata
    
    metadata['extraction_method'] = 'advanced'
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
        """Handle the valid form data."""
        video = form.save(commit=False)
        video.uploader = self.request.user
        video.save()
        form.save_m2m()  # For saving ManyToMany relations like tags
        messages.success(self.request, f"Video '{video.title}' has been successfully processed.")
        return super().form_valid(form)
            
    def form_invalid(self, form):
        """Handle the invalid form data."""
        logger = logging.getLogger(__name__)
        logger.error(f"Error in form_invalid: {form.errors}")
        messages.error(self.request, f"Error uploading video: {str(form.errors)}")
        return super().form_invalid(form)

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
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(f"Error extracting metadata: {str(e)}")
                
                # Create basic metadata from the file information
                basic_metadata = {
                    'file_size': os.path.getsize(temp_path) if os.path.exists(temp_path) else video_file.size,
                    'format': os.path.splitext(video_file.name)[1].strip('.').upper(),
                    'mime_type': video_file.content_type,
                    'extraction_method': 'fallback',
                    'error_message': str(e)
                }
                
                # Convert file size to human-readable format
                size_bytes = basic_metadata['file_size']
                if size_bytes < 1024 * 1024:  # Less than 1MB
                    basic_metadata['file_size_display'] = f"{size_bytes / 1024:.1f} KB"
                else:  # MB or GB
                    size_mb = size_bytes / (1024 * 1024)
                    if size_mb < 1024:
                        basic_metadata['file_size_display'] = f"{size_mb:.1f} MB"
                    else:
                        basic_metadata['file_size_display'] = f"{size_mb / 1024:.2f} GB"
                
                # Return limited metadata with a warning
                return JsonResponse({
                    'success': True,
                    'metadata': basic_metadata,
                    'warning': 'Limited metadata available due to extraction issues'
                })
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