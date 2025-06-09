from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.conf import settings

@method_decorator(login_required, name='dispatch')
class UploadPageView(TemplateView):
    """
    Renders the main video upload page.
    This view's primary responsibility is to inject necessary configuration,
    like the API Gateway URL, into the template context for the frontend.
    """
    template_name = 'upload.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Inject the API Gateway URL from settings into the template
        context['API_GATEWAY_URL'] = settings.API_GATEWAY_URL
        return context 