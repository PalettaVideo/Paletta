from django.views.generic import TemplateView, FormView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views import View
from ..models import Video, Tag
from django import forms
import os
import subprocess
import json

class VideoUploadForm(forms.ModelForm):
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
        # Create video object but don't save to DB yet
        video = form.save(commit=False)
        video.uploader = self.request.user
        
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
                    # TODO: need to handle this not simply passing duration as none
                    pass
                    
        except Exception as e:
            # Log the error but continue
            print(f"Error extracting video metadata: {e}")
        
        # Save again with the updated metadata
        video.save()
        
        return super().form_valid(form)

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
            
            # Create video object
            video = Video(
                title=title,
                description=description,
                category_id=category_id,
                uploader=request.user,
                video_file=video_file,
                thumbnail=thumbnail,
                is_published=is_published
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
                        # TODO: need to handle this not simply passing duration as none
                        pass
            except Exception as e:
                print(f"Error extracting video metadata: {e}")
            
            # Save again with metadata
            video.save()
            
            return JsonResponse({
                'success': True,
                'video_id': video.id,
                'message': 'Video uploaded successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error uploading video: {str(e)}'
            }, status=500) 