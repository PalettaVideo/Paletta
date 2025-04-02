from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
import json
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Library, UserLibraryRole
from .serializers import LibrarySerializer, UserLibraryRoleSerializer
from videos.serializers import CategorySerializer
from videos.models import Category
import base64
import os
from django.core.files.base import ContentFile
from django.conf import settings
from django.urls import reverse
from django.contrib import messages

# Create your views here.

class IsLibraryAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow library administrators to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the library administrator
        return obj.owner == request.user

class LibraryViewSet(viewsets.ModelViewSet):
    queryset = Library.objects.all()
    serializer_class = LibrarySerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsLibraryAdminOrReadOnly]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """Close (delete) a library"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'success': True,
            'message': 'Library closed successfully.'
        }, status=status.HTTP_200_OK)
        
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Toggle a library's active status"""
        library = self.get_object()
        
        # Only the library administrator can change the status
        if library.owner != request.user:
            return Response(
                {"error": "Only the library administrator can change the library status."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Get the desired status from the request
        active = request.data.get('active', not library.is_active)
        
        # Update the library status
        library.is_active = active
        library.save(update_fields=['is_active'])
        
        return Response({
            'success': True,
            'is_active': library.is_active,
            'message': f"Library {'started' if active else 'stopped'} successfully."
        }, status=status.HTTP_200_OK)
        
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        library = self.get_object()
        
        # Only the library administrator can add members
        if library.owner != request.user:
            return Response(
                {"detail": "Only the library administrator can add members."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'contributor')
        
        if not user_id:
            return Response(
                {"detail": "User ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check if the user is already a member
        if UserLibraryRole.objects.filter(library=library, user_id=user_id).exists():
            return Response(
                {"detail": "User is already a member of this library."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Create the library member
        user_role = UserLibraryRole.objects.create(
            library=library,
            user_id=user_id,
            role=role
        )
        
        serializer = UserLibraryRoleSerializer(user_role)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class UserLibraryRoleViewSet(viewsets.ModelViewSet):
    queryset = UserLibraryRole.objects.all()
    serializer_class = UserLibraryRoleSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

def process_base64_image(base64_data, name=None):
    """
    Process base64 image data and convert it to a Django ContentFile
    """
    # Remove header if present
    if ',' in base64_data:
        format, imgstr = base64_data.split(';base64,')
        ext = format.split('/')[-1]
    else:
        # Assume it's already properly formatted
        imgstr = base64_data
        ext = 'png'  # Default extension
    
    # Generate a random filename if none provided
    if not name:
        import uuid
        name = f"{uuid.uuid4()}.{ext}"
    elif not name.endswith(f'.{ext}'):
        name = f"{name}.{ext}"
    
    # Decode base64 and create ContentFile
    data = base64.b64decode(imgstr)
    return ContentFile(data, name=name)

class CreateLibraryView(LoginRequiredMixin, TemplateView):
    template_name = 'create_library_admin.html'
    
    def post(self, request, *args, **kwargs):
        try:
            # Log received data for debugging
            print("POST data:", request.POST)
            print("FILES:", request.FILES)
            
            data = {
                'name': request.POST.get('name'),
                'description': request.POST.get('description'),
                # Other fields as needed
            }
            
            # Handle color
            primary_color = request.POST.get('primary_color')
            if primary_color:
                data['color_scheme'] = {
                    'primary': primary_color,
                    'secondary': '#FFFFFF',
                    'text': '#000000'
                }
                
            # First, process any categories
            categories = []
            categories_json = request.POST.get('categories_json')
            print(f"Raw categories_json: {categories_json}")
            
            if categories_json and categories_json != '[]':
                try:
                    categories_data = json.loads(categories_json)
                    print(f"Parsed categories data (count: {len(categories_data)}): {categories_data}")
                    
                    for category_data in categories_data:
                        print(f"Processing category: {category_data.get('name')}")
                        # Create category data dict for serializer
                        category_dict = {
                            'name': category_data.get('name'),
                            'description': category_data.get('description')
                        }
                        
                        # Use the CategorySerializer from videos app
                        category_serializer = CategorySerializer(data=category_dict)
                        if category_serializer.is_valid():
                            print(f"Category {category_data.get('name')} validated successfully")
                            # Save the category
                            category = category_serializer.save()
                            
                            # Handle category image if provided as base64
                            if 'image' in category_data and category_data['image'].startswith('data:image'):
                                print(f"Processing image for category {category_data.get('name')}")
                                try:
                                    # Convert base64 to file and save
                                    image_file = process_base64_image(
                                        category_data['image'], 
                                        name=f"category_{category_data.get('name', 'unnamed')}"
                                    )
                                    category.image = image_file
                                    category.save()
                                    print(f"Image saved for category {category_data.get('name')}")
                                except Exception as e:
                                    print(f"Error saving category image: {e}")
                            else:
                                print(f"No valid image found for category {category_data.get('name')}")
                            
                            categories.append(category)
                        else:
                            print(f"Category validation errors for {category_data.get('name')}: {category_serializer.errors}")
                            return JsonResponse({
                                'status': 'error',
                                'message': f"Category validation failed: {category_serializer.errors}"
                            }, status=400)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {str(e)}")
                    return JsonResponse({
                        'status': 'error',
                        'message': f"Invalid category data format: {str(e)}"
                    }, status=400)
            else:
                print("No categories provided or empty categories array")
                
            # Then create the library
            serializer = LibrarySerializer(data=data)
            if serializer.is_valid():
                # Save with owner set to the current user
                library = serializer.save(owner=request.user)
                
                # Handle logo upload if provided
                logo = request.FILES.get('logo')
                if logo:
                    library.logo = logo
                    library.save()
                
                # If any videos belong to the library, associate them with the created categories
                if categories and hasattr(library, 'videos'):
                    for video in library.videos.all():
                        # Check if video doesn't already have a category
                        if not video.category:
                            # Assign the first category as default
                            video.category = categories[0]
                            video.save()
                
                # Create an admin role for the creator automatically
                UserLibraryRole.objects.create(
                    library=library,
                    user=request.user,
                    role='admin'
                )
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Library created successfully.',
                    'redirect_url': reverse('manage_libraries')
                })
            else:
                print(f"Library validation errors: {serializer.errors}")
                return JsonResponse({
                    'status': 'error',
                    'message': f"Library validation failed: {serializer.errors}"
                }, status=400)
                
        except Exception as e:
            print(f"Error creating library: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f"An error occurred: {str(e)}"
            }, status=500)

class ManageLibrariesView(LoginRequiredMixin, TemplateView):
    template_name = 'manage_libraries.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all libraries where the user is either the owner or has a role
        user_libraries = Library.objects.filter(owner=self.request.user)
        context['libraries'] = user_libraries
        
        # Get libraries where the user is a contributor
        contributed_libraries = Library.objects.filter(
            user_roles__user=self.request.user
        ).exclude(owner=self.request.user)
        context['contributed_libraries'] = contributed_libraries
        
        return context

class EditLibraryView(LoginRequiredMixin, TemplateView):
    template_name = 'edit_library_admin.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get library_id from kwargs or from query parameters
        library_id = kwargs.get('library_id') or self.request.GET.get('library_id')
        
        if not library_id:
            context['error'] = "No library specified"
            return context
            
        try:
            library = Library.objects.get(id=library_id)
            
            # Check if user can edit this library
            if not (library.owner == self.request.user or 
                    UserLibraryRole.objects.filter(library=library, user=self.request.user, role='admin').exists()):
                context['permission_error'] = True
                context['library_name'] = library.name
                return context
            
            context['library'] = library
            # Get categories for this library
            context['categories'] = Category.objects.filter(library=library)
            
            # Get contributors for this library
            context['contributors'] = UserLibraryRole.objects.filter(
                library=library
            ).select_related('user')
            
        except Library.DoesNotExist:
            context['library_not_found'] = True
            context['library_name'] = f"ID: {library_id}"
        
        return context
    
    def post(self, request, *args, **kwargs):
        # Get library_id from kwargs or from request parameters
        library_id = kwargs.get('library_id') or request.POST.get('library_id')
        
        if not library_id:
            return JsonResponse({
                'status': 'error',
                'message': "No library specified"
            }, status=400)
            
        try:
            library = Library.objects.get(id=library_id)
            
            # Check if user can edit this library
            if not (library.owner == self.request.user or 
                    UserLibraryRole.objects.filter(library=library, user=self.request.user, role='admin').exists()):
                return JsonResponse({
                    'status': 'error',
                    'message': "You don't have permission to edit this library."
                }, status=403)
            
            # Update library fields
            library_name = request.POST.get('library_name')
            if library_name:
                library.name = library_name
                
            description = request.POST.get('description')
            if description:
                library.description = description
                
            # Handle theme color
            theme_color = request.POST.get('theme_color')
            if theme_color:
                if not library.color_scheme:
                    library.color_scheme = {}
                library.color_scheme['primary'] = theme_color
                
            # Handle logo if provided
            if request.FILES.get('logo'):
                library.logo = request.FILES['logo']
                
            library.save()
            
            # Process categories
            if 'categories' in request.POST:
                try:
                    categories_data = json.loads(request.POST.get('categories'))
                    
                    # Keep track of existing category IDs
                    current_categories = set(Category.objects.filter(library=library).values_list('id', flat=True))
                    processed_categories = set()
                    
                    for category_data in categories_data:
                        category_id = category_data.get('id')
                        
                        if category_id and not category_id.startswith('temp_'):
                            # Update existing category
                            try:
                                category = Category.objects.get(id=category_id, library=library)
                                category.name = category_data.get('name', category.name)
                                category.description = category_data.get('description', category.description)
                                
                                # Handle image if provided
                                if 'image' in category_data and category_data['image'] and category_data['image'].startswith('data:'):
                                    image_file = process_base64_image(
                                        category_data['image'],
                                        name=f"category_{category.name}"
                                    )
                                    category.image = image_file
                                    
                                category.save()
                                processed_categories.add(int(category_id))
                                
                            except Category.DoesNotExist:
                                pass  # Category might belong to another library or doesn't exist
                        else:
                            # Create new category
                            new_category = Category(
                                name=category_data.get('name'),
                                description=category_data.get('description', ''),
                                library=library
                            )
                            new_category.save()
                            
                            # Handle image if provided
                            if 'image' in category_data and category_data['image'] and category_data['image'].startswith('data:'):
                                image_file = process_base64_image(
                                    category_data['image'],
                                    name=f"category_{new_category.name}"
                                )
                                new_category.image = image_file
                                new_category.save()
                                
                            processed_categories.add(new_category.id)
                    
                    # Delete categories that were removed
                    categories_to_delete = current_categories - processed_categories
                    if categories_to_delete:
                        Category.objects.filter(id__in=categories_to_delete, library=library).delete()
                        
                except json.JSONDecodeError:
                    return JsonResponse({
                        'status': 'error',
                        'message': "Invalid category data format"
                    }, status=400)
            
            # Process contributors
            if 'contributors' in request.POST:
                try:
                    contributors_data = json.loads(request.POST.get('contributors'))
                    
                    # Keep track of existing contributor IDs
                    current_contributors = set(UserLibraryRole.objects.filter(
                        library=library, 
                        role='contributor'
                    ).values_list('id', flat=True))
                    
                    processed_contributors = set()
                    
                    for contributor_data in contributors_data:
                        contributor_id = contributor_data.get('id')
                        
                        if contributor_id and not contributor_id.startswith('temp_'):
                            # Existing contributor - just mark as processed
                            processed_contributors.add(int(contributor_id))
                        else:
                            # New contributor to add
                            from django.contrib.auth import get_user_model
                            User = get_user_model()
                            
                            # Try to find user by email
                            try:
                                user = User.objects.get(email=contributor_data.get('email'))
                                
                                # Check if user already has a role in this library
                                if not UserLibraryRole.objects.filter(library=library, user=user).exists():
                                    role = UserLibraryRole.objects.create(
                                        library=library,
                                        user=user,
                                        role='contributor'
                                    )
                                    processed_contributors.add(role.id)
                            except User.DoesNotExist:
                                # User doesn't exist - we might want to invite them
                                # For now, just log it
                                print(f"User with email {contributor_data.get('email')} not found")
                    
                    # Remove contributors that were removed
                    contributors_to_delete = current_contributors - processed_contributors
                    if contributors_to_delete:
                        UserLibraryRole.objects.filter(id__in=contributors_to_delete, library=library).delete()
                        
                except json.JSONDecodeError:
                    return JsonResponse({
                        'status': 'error',
                        'message': "Invalid contributor data format"
                    }, status=400)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Library updated successfully',
                'redirect_url': reverse('manage_libraries')
            })
            
        except Library.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': "Library not found"
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
