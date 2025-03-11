from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from videos.models import Category
from videos.serializers import CategorySerializer

class HomeView(TemplateView):
    """Home view that serves the appropriate home page based on user authentication."""
    
    def get(self, request, *args, **kwargs):
        """Serve the appropriate home page."""
        if request.user.is_authenticated:
            # Fetch all categories from the database
            categories = Category.objects.all().order_by('name')
            
            # Use the serializer to get proper image URLs
            serializer = CategorySerializer(categories, many=True, context={'request': request})
            
            context = {
                'categories': serializer.data
            }
            
            # TODO: see which of these functionalities are needed and can be loaded from the .js static files
            # TODO: see if the user role check is needed for the home page
            if request.user.role in ['admin', 'owner']:
                return render(request, 'homepage_internal.html', context)
            elif request.user.role == 'contributor':
                return render(request, 'homepage_internal.html', context) 
                # TODO: create a specific contributor page
            else:
                return render(request, 'homepage_internal.html', context)
                # TODO: create a specific customer page
        else:
            return render(request, 'homepage_external.html')

class LogoutView(TemplateView):
    """View to handle user logout."""
    
    def get(self, request, *args, **kwargs):
        """Log the user out and redirect to login page."""
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('login')
