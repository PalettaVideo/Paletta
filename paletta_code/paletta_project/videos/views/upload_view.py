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
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = "Select a category"
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

class UploadView(FormView):
    """View for the video upload page."""
    template_name = 'upload.html'
    form_class = VideoUploadForm
    success_url = reverse_lazy('upload_history')
    
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """Serve the upload page."""
        return super().get(request, *args, **kwargs)
    
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
            
            # Save to get an ID for the video
            video.save()
            
            # Process tags (if any)
            tags_text = form.cleaned_data.get('tags', '')
            if tags_text:
                tag_names = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    video.tags.add(tag)
            
            # Extract video metadata if ffprobe is available
            try:
                if video.video_file and os.path.exists(video.video_file.path):
                    # Get file size
                    video.file_size = os.path.getsize(video.video_file.path)
                    
                    # Try to get duration using ffprobe if available
                    try:
                        cmd = [
                            'ffprobe', 
                            '-v', 'error', 
                            '-show_entries', 'format=duration', 
                            '-of', 'json', 
                            video.video_file.path
                        ]
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        if result.returncode == 0:
                            data = json.loads(result.stdout)
                            duration = float(data['format']['duration'])
                            video.duration = int(duration)
                    except (subprocess.SubprocessError, json.JSONDecodeError, KeyError, FileNotFoundError):
                        # If ffprobe fails or isn't installed
                        pass
                        
            except Exception as e:
                # Log the error but continue
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error extracting video metadata: {e}")
            
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
        try:
            # Extract data from request
            title = request.POST.get('title')
            description = request.POST.get('description')
            category_id = request.POST.get('category')
            tags_text = request.POST.get('tags', '')
            video_file = request.FILES.get('video_file')
            thumbnail = request.FILES.get('thumbnail')
            is_published = request.POST.get('is_published', 'true').lower() == 'true'
            
            # Validate required fields
            if not all([title, category_id, video_file]):
                return JsonResponse({
                    'success': False,
                    'message': 'Missing required fields'
                }, status=400)
            
            # Validate file size (limit to 5GB)
            # TODO: discuss individual file limits with owner
            max_size = 5 * 1024 * 1024 * 1024  # 5GB in bytes
            if video_file.size > max_size:
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
            
            # Save to get an ID
            video.save()
            
            # Process tags
            if tags_text:
                tag_names = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    video.tags.add(tag)
            
            # Extract metadata (similar to form view)
            try:
                if video.video_file and os.path.exists(video.video_file.path):
                    # Get file size
                    video.file_size = os.path.getsize(video.video_file.path)
                    
                    # Try to get duration using ffprobe if available
                    try:
                        cmd = [
                            'ffprobe', 
                            '-v', 'error', 
                            '-show_entries', 'format=duration', 
                            '-of', 'json', 
                            video.video_file.path
                        ]
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        if result.returncode == 0:
                            data = json.loads(result.stdout)
                            duration = float(data['format']['duration'])
                            video.duration = int(duration)
                    except (subprocess.SubprocessError, json.JSONDecodeError, KeyError, FileNotFoundError):
                        # If ffprobe fails or isn't installed
                        pass
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error extracting video metadata: {e}")
            
            # Save again with metadata
            video.save()
            
            # Log the upload
            VideoLogService.log_upload(video, request.user, request)
            
            # Queue the video for upload to AWS S3 storage
            upload_video_to_storage.delay(video.id)
            
            return JsonResponse({
                'success': True,
                'video_id': video.id,
                'message': 'Video uploaded successfully and queued for AWS S3 storage'
            })
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in VideoAPIUploadView.post: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Error uploading video: {str(e)}'
            }, status=500) 