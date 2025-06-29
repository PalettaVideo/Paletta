from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib import messages
from ..models import User

class SignupView(TemplateView):
    """Custom signup view that serves the signup.html file."""
    def get(self, request, *args, **kwargs):
        # serve the signup.html file
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, 'signup.html')
    
    def post(self, request, *args, **kwargs):
        # handle signup form submission - get form data from the request
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        institution = request.POST.get('institution', '')
        company = request.POST.get('company', '')
        
        # validate form data
        if not email or not first_name or not last_name or not password or not confirm_password:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'signup.html')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'signup.html')
        
        # check if user already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
            return render(request, 'signup.html')
        
        # create user
        try:
            user = User.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
                institution=institution,
                company=company,
                role='contributor'
            )
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'signup.html')
