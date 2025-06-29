from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone

class UserManager(BaseUserManager):
  # define a model manager for the User model with email as the unique identifier

  def create_user(self, email, password=None, **extra_fields):
    # create and save a User with the given email and password
    if not email:
        raise ValueError('The Email field must be set')
    email = self.normalize_email(email)
    # set username to email to avoid unique constraint issues 
    extra_fields.setdefault('username', email)
    user = self.model(email=email, **extra_fields)
    user.set_password(password)
    user.save(using=self._db)
    return user

  def create_superuser(self, email, password=None, **extra_fields):
    # create and save a SuperUser with the given email and password
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
  # define the roles for the users
  # TODO: discuss with the team if we need to add more roles!
  ROLE_CHOICES = [
    ('owner', 'Owner'),
    ('admin', 'Administrator'),
    ('contributor', 'Contributor'),
  ]

  # define the fields for the user
  email = models.EmailField(unique=True)
  first_name = models.CharField(max_length=30, blank=False) 
  last_name = models.CharField(max_length=30, blank=False)   
  institution = models.CharField(max_length=50, blank=True)
  company = models.CharField(max_length=50, blank=True, null=True)
  role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='contributor')
  created_at = models.DateTimeField(default=timezone.now)

  USERNAME_FIELD = 'email'
  REQUIRED_FIELDS = ['first_name', 'last_name']  # required fields to create a superuser

  objects = UserManager()

  def __str__(self):
    # return the email of the user
    return self.email

  def get_full_name(self):
    # return the full name of the user
    return f"{self.first_name} {self.last_name}"
