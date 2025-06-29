from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from ..models import Video

class UploadHistoryView(TemplateView):
    """View for the upload history page."""
    template_name = 'upload_history.html'
    
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """Serve the upload history page with the user's videos."""
        context = self.get_context_data(**kwargs)
        # Use select_related and prefetch_related to efficiently fetch related information
        context['videos'] = Video.objects.filter(uploader=request.user).select_related(
            'library', 'subject_area'
        ).prefetch_related('content_types').order_by('-upload_date')
        return self.render_to_response(context)