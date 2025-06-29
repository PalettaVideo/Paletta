from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

class CustomLoginView(TemplateView):
    """
    BACKEND/FRONTEND-READY: User authentication login interface.
    MAPPED TO: /login/ URL
    USED BY: login.html template
    
    Handles user login with email-based authentication and redirects.
    """
    
    def get(self, request, *args, **kwargs):
        """
        BACKEND/FRONTEND-READY: Display login form.
        MAPPED TO: GET /login/
        USED BY: Login page access and navigation
        
        Shows login form or redirects to home if already authenticated.
        """
        if request.user.is_authenticated:
            return redirect('home')  
        return render(request, 'login.html')
    
    def post(self, request, *args, **kwargs):
        """
        BACKEND/FRONTEND-READY: Process login form submission.
        MAPPED TO: POST /login/
        USED BY: login.html form submission
        
        Authenticates user with email/password and handles login flow.
        Required fields: email, password
        """
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, 'Please enter both email and password.')
            return render(request, 'login.html')
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid email or password.')
            return render(request, 'login.html')
