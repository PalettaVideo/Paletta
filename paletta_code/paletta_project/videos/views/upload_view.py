from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from ..models import Video

class MyVideosView(TemplateView):
    """View for the my videos page."""
    template_name = 'my_videos.html'
    
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """Serve the my videos page with the user's videos."""
        context = self.get_context_data(**kwargs)
        # Use select_related and prefetch_related to efficiently fetch related information
        context['videos'] = Video.objects.filter(uploader=request.user).select_related(
            'library', 'content_type'
        ).order_by('-upload_date')
        return self.render_to_response(context)