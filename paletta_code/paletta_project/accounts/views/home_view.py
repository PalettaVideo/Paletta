from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from videos.models import Category
from videos.serializers import CategorySerializer

class HomeView(TemplateView):
    """Home view that serves the unified home page with conditional content based on authentication."""
    
    def get(self, request, *args, **kwargs):
        """Serve the home page with appropriate context."""
        context = {}
        
        if request.user.is_authenticated:
            # Fetch all categories from the database
            categories = Category.objects.all().order_by('name')
            
            # Use the serializer to get proper image URLs
            serializer = CategorySerializer(categories, many=True, context={'request': request})
            
            context = {
                'categories': serializer.data
            }
        
        # Return the single homepage template with the context
        return render(request, 'homepage.html', context)

class LogoutView(TemplateView):
    """View to handle user logout."""
    
    def get(self, request, *args, **kwargs):
        """Log the user out and redirect to login page."""
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('login')
