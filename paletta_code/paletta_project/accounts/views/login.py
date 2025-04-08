from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

class CustomLoginView(TemplateView):
    """Custom login view that serves the login.html file."""
    
    def get(self, request, *args, **kwargs):
        """Serve the login.html file."""
        if request.user.is_authenticated:
            # redirect to home if already logged in
            return redirect('home')  
        return render(request, 'login.html')
    
    def post(self, request, *args, **kwargs):
        """Handle login form submission."""
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, 'Please enter both email and password.')
            return render(request, 'login.html')
        
        # authenticate with email
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            
            # redirect based on user role
            if user.role in ['admin', 'owner']:
                return redirect('home')  # TODO: create a specific admin home
            elif user.role == 'contributor':
                return redirect('home')  # TODO: create a specific contributor home
            else:
                return redirect('home')
        else:
            messages.error(request, 'Invalid email or password.')
            return render(request, 'login.html')
