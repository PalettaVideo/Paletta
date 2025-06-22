from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
import json
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
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
from accounts.models import User

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
        try:
            instance = self.get_object()
            
            # Check if user has permission to delete this library
            if instance.owner != request.user and not UserLibraryRole.objects.filter(
                library=instance, user=request.user, role='admin'
            ).exists():
                return Response({
                    'status': 'error',
                    'message': 'You do not have permission to delete this library.'
                }, status=403)
            
            self.perform_destroy(instance)
            return Response({
                'status': 'success',
                'message': 'Library deleted successfully.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=500)
        
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Toggle library active/inactive status"""
        try:
            library = self.get_object()
            
            # Check if user has permission to modify this library
            if library.owner != request.user and not UserLibraryRole.objects.filter(
                library=library, user=request.user, role='admin'
            ).exists():
                return Response({
                    'status': 'error',
                    'message': 'You do not have permission to modify this library.'
                }, status=403)
            
            # Toggle the status
            library.is_active = not library.is_active
            library.save()
            
            status_text = 'activated' if library.is_active else 'deactivated'
            return Response({
                'status': 'success',
                'message': f'Library has been {status_text} successfully.',
                'is_active': library.is_active
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=500)

    @action(detail=True, methods=['post'])
    def add_categories(self, request, pk=None):
        """Add custom categories to a library"""
        try:
            library = self.get_object()
            
            # Check if user has permission to modify this library
            if library.owner != request.user and not UserLibraryRole.objects.filter(
                library=library, user=request.user, role='admin'
            ).exists():
                return Response({
                    'status': 'error',
                    'message': 'You do not have permission to modify this library.'
                }, status=403)
            
            # Check if library uses custom categories
            if library.category_source != 'custom':
                return Response({
                    'status': 'error',
                    'message': 'This library does not use custom categories.'
                }, status=400)
            
            categories_data = request.data.get('categories', [])
            if not categories_data:
                return Response({
                    'status': 'error',
                    'message': 'No categories provided.'
                }, status=400)
            
            # Import here to avoid circular imports
            from videos.models import Category
            
            created_categories = []
            for category_data in categories_data:
                # Create the category
                category_kwargs = {
                    'subject_area': category_data.get('subject_area'),
                    'description': category_data.get('description', ''),
                    'library': library,
                    'is_active': True
                }
                
                # Add custom_name if it's a custom category
                if category_data.get('subject_area') == 'custom' and category_data.get('custom_name'):
                    category_kwargs['custom_name'] = category_data.get('custom_name')
                
                category = Category.objects.create(**category_kwargs)
                created_categories.append(category)
            
            return Response({
                'status': 'success',
                'message': f'Successfully added {len(created_categories)} categories.',
                'created_count': len(created_categories)
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=500)

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
            # Get category source selection
            category_source = request.POST.get('category_source', 'custom')
            
            data = {
                'name': request.POST.get('name'),
                'description': request.POST.get('description'),
                'category_source': category_source,
                'storage_tier': request.POST.get('storage_tier', 'basic'),
            }
            
            # Handle color
            primary_color = request.POST.get('primary_color')
            if primary_color:
                data['color_scheme'] = {
                    'primary': primary_color,
                    'secondary': '#FFFFFF',
                    'text': '#000000'
                }
            
            # Create the library first
            serializer = LibrarySerializer(data=data)
            if serializer.is_valid():
                # Save with owner set to the current user
                library = serializer.save(owner=request.user)
                
                # Handle logo upload if provided
                logo = request.FILES.get('logo')
                if logo:
                    library.logo = logo
                    library.save()
                
                # Categories are automatically set up by Library.save() method
                
                # For custom libraries, handle any additional selected subject areas
                if category_source == 'custom':
                    # Get selected subject areas from checkboxes
                    custom_subject_areas = request.POST.getlist('custom_subject_areas')
                    
                    if custom_subject_areas:
                        from videos.models import Category
                        
                        # Create categories for each selected subject area
                        for subject_area in custom_subject_areas:
                            # Convert subject area code to display name
                            display_name = subject_area.replace('_', ' ').title()
                            
                            Category.objects.get_or_create(
                                subject_area=subject_area,
                                library=library,
                                defaults={
                                    'description': f'{display_name} category for {library.name}',
                                    'is_active': True
                                }
                            )
                
                # Create an admin role for the creator automatically
                UserLibraryRole.objects.create(
                    library=library,
                    user=request.user,
                    role='admin'
                )
                
                messages.success(request, f'Library "{library.name}" created successfully!')
                return redirect('manage_libraries')
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': f"Library validation failed: {serializer.errors}"
                }, status=400, content_type='application/json')
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f"An error occurred: {str(e)}"
            }, status=500, content_type='application/json')

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
            
            # Check if the user has permission to edit this library
            if library.owner != self.request.user and not self.request.user.is_superuser:
                context['permission_error'] = True
                context['library_name'] = library.name
                return context
            
            context['library'] = library
            
            # Get categories for this library - ALWAYS include all library categories (including Private)
            categories = Category.objects.filter(library=library, is_active=True).order_by('subject_area')
            
            # Separate Private category to show it first
            private_category = None
            other_categories = []
            
            for category in categories:
                if category.subject_area == 'private':
                    private_category = category
                else:
                    other_categories.append(category)
            
            # Combine with Private first
            ordered_categories = []
            if private_category:
                ordered_categories.append(private_category)
            ordered_categories.extend(other_categories)
            
            context['categories'] = ordered_categories
            
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
            }, status=400, content_type='application/json')
            
        try:
            library = Library.objects.get(id=library_id)
            
            # Check if user can edit this library
            if not (library.owner == self.request.user or 
                    UserLibraryRole.objects.filter(library=library, user=self.request.user, role='admin').exists()):
                return JsonResponse({
                    'status': 'error',
                    'message': "You don't have permission to edit this library."
                }, status=403, content_type='application/json')
            
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
                                # Note: Category name is now handled through subject_area enum
                                category.description = category_data.get('description', category.description)
                                
                                # Handle image if provided
                                if 'image' in category_data and category_data['image'] and category_data['image'].startswith('data:'):
                                    image_file = process_base64_image(
                                        category_data['image'],
                                        name=f"category_{category.display_name}"
                                    )
                                    category.image = image_file
                                    
                                category.save()
                                processed_categories.add(int(category_id))
                                
                            except Category.DoesNotExist:
                                pass  # Category might belong to another library or doesn't exist
                        else:
                            # Create new category
                            new_category = Category(
                                subject_area=category_data.get('subject_area'),
                                description=category_data.get('description', ''),
                                library=library
                            )
                            new_category.save()
                            
                            # Handle image if provided
                            if 'image' in category_data and category_data['image'] and category_data['image'].startswith('data:'):
                                image_file = process_base64_image(
                                    category_data['image'],
                                    name=f"category_{new_category.display_name}"
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
                    }, status=400, content_type='application/json')
            
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
                                pass  # User not found
                    
                    # Remove contributors that were removed
                    contributors_to_delete = current_contributors - processed_contributors
                    if contributors_to_delete:
                        UserLibraryRole.objects.filter(id__in=contributors_to_delete, library=library).delete()
                        
                except json.JSONDecodeError:
                    return JsonResponse({
                        'status': 'error',
                        'message': "Invalid contributor data format"
                    }, status=400, content_type='application/json')
            
            return JsonResponse({
                'status': 'success',
                'message': 'Library updated successfully',
                'redirect_url': reverse('manage_libraries')
            }, content_type='application/json')
            
        except Library.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': "Library not found"
            }, status=404, content_type='application/json')
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500, content_type='application/json')
