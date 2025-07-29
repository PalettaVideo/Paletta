from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone

class UserManager(BaseUserManager):
  """
  BACKEND-READY: Custom user manager for email-based authentication.
  MAPPED TO: User model manager
  USED BY: User.objects queries and user creation
  
  Manages user creation with email as unique identifier instead of username.
  """

  def create_user(self, email, password=None, **extra_fields):
    """
    BACKEND-READY: Create and save a regular user with email and password.
    MAPPED TO: User creation process
    USED BY: User registration and admin user creation
    
    Creates user with email as primary identifier and sets username to email.
    Required fields: email, password
    """
    if not email:
        raise ValueError('The Email field must be set')
    email = self.normalize_email(email)
    extra_fields.setdefault('username', email)
    user = self.model(email=email, **extra_fields)
    user.set_password(password)
    user.save(using=self._db)
    return user

  def create_superuser(self, email, password=None, **extra_fields):
    """
    BACKEND-READY: Create and save a superuser with admin privileges.
    MAPPED TO: Django admin and management commands
    USED BY: Admin user creation and deployment scripts
    
    Creates superuser with full permissions and admin role.
    Required fields: email, password
    """
    extra_fields.setdefault('is_staff', True)
    extra_fields.setdefault('is_superuser', True)
    extra_fields.setdefault('is_active', True)
    extra_fields.setdefault('role', 'admin')

    if extra_fields.get('is_staff') is not True:
        raise ValueError('Superuser must have is_staff=True.')
    if extra_fields.get('is_superuser') is not True:
        raise ValueError('Superuser must have is_superuser=True.')

    return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
  """
  BACKEND/FRONTEND-READY: Custom user model with role-based access control.
  MAPPED TO: /api/users/ endpoints and authentication system
  USED BY: All authentication, authorization, and user management features
  
  Extends Django's AbstractUser with email-based auth and role management.
  """
  ROLE_CHOICES = [
    ('owner', 'Owner'),
    ('admin', 'Administrator'),
    ('user', 'User'),
  ]

  email = models.EmailField(unique=True)
  first_name = models.CharField(max_length=30, blank=False) 
  last_name = models.CharField(max_length=30, blank=False)   
  institution = models.CharField(max_length=50, blank=True)
  company = models.CharField(max_length=50, blank=True, null=True)
  role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
  created_at = models.DateTimeField(default=timezone.now)

  USERNAME_FIELD = 'email'
  REQUIRED_FIELDS = ['first_name', 'last_name']

  objects = UserManager()

  def __str__(self):
    """
    BACKEND/FRONTEND-READY: String representation of user.
    MAPPED TO: Admin interface and string conversions
    USED BY: Django admin, logging, and debugging
    
    Returns user's email as primary identifier.
    """
    return self.email

  def get_full_name(self):
    """
    BACKEND/FRONTEND-READY: Get user's full name.
    MAPPED TO: Template context and API responses
    USED BY: Frontend display and user profile rendering
    
    Returns formatted full name from first and last name fields.
    """
    return f"{self.first_name} {self.last_name}"
