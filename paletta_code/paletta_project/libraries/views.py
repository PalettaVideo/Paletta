from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
import json
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Library, UserLibraryRole
from .serializers import LibrarySerializer, UserLibraryRoleSerializer
from videos.models import ContentType
import base64
from django.core.files.base import ContentFile
from django.urls import reverse
from django.contrib import messages

# Create your views here.

class IsLibraryAdminOrReadOnly(permissions.BasePermission):
    """
    BACKEND-READY: Custom permission for library administration.
    MAPPED TO: Library API endpoints
    USED BY: LibraryViewSet permission checking
    
    Allows read access to all, write access only to library owners.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user

class LibraryViewSet(viewsets.ModelViewSet):
    """
    BACKEND/FRONTEND-READY: Complete CRUD operations for library management.
    MAPPED TO: /api/libraries/ endpoints
    USED BY: Frontend library management interface and admin tools
    
    Provides library creation, reading, updating, deletion, and custom actions.
    """
    queryset = Library.objects.all()
    serializer_class = LibrarySerializer
    
    def get_permissions(self):
        """
        BACKEND-READY: Dynamic permission assignment based on action.
        MAPPED TO: DRF permission system
        USED BY: All library API endpoints
        
        Sets appropriate permissions for different CRUD operations.
        """
        permission_map = {
            'create': [permissions.IsAuthenticated],
            'update': [IsLibraryAdminOrReadOnly],
            'partial_update': [IsLibraryAdminOrReadOnly],
            'destroy': [IsLibraryAdminOrReadOnly],
        }
        permission_classes = permission_map.get(self.action, [permissions.AllowAny])
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """
        BACKEND-READY: Set library owner during creation.
        MAPPED TO: POST /api/libraries/
        USED BY: Library creation endpoint
        
        Automatically assigns current user as library owner.
        """
        serializer.save(owner=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """
        BACKEND-READY: Delete library with permission validation.
        MAPPED TO: DELETE /api/libraries/{id}/
        USED BY: Library management interface
        
        Removes library after validating user permissions.
        """
        try:
            instance = self.get_object()
            
            # Check if this is the Paletta library
            is_paletta_library = instance.is_paletta_library
            
            # Permission check: Paletta library can only be deleted by system superusers or users with owner role
            if is_paletta_library and not (request.user.is_superuser or request.user.role == 'owner'):
                return Response({
                    'status': 'error',
                    'message': 'Only users with owner-level access or System Superuser can delete the Paletta library.'
                }, status=403)
            
            # Permission check: Other libraries can be deleted by owners or the library creator
            if not is_paletta_library:
                is_owner = request.user.is_superuser or request.user.role == 'owner'
                is_creator = instance.owner == request.user
                is_admin = UserLibraryRole.objects.filter(
                    library=instance, user=request.user, role='admin'
                ).exists()
                
                if not (is_owner or is_creator or is_admin):
                    return Response({
                        'status': 'error',
                        'message': 'Only users with owner-level access or System Superuser can delete this library.'
                    }, status=403)
            
            self.perform_destroy(instance)
            return Response({
                'status': 'success',
                'message': 'Library deleted successfully.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=500)
        
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """
        BACKEND-READY: Toggle library active/inactive status.
        MAPPED TO: POST /api/libraries/{id}/toggle_status/
        USED BY: Library management interface
        
        Switches library between active and inactive states.
        """
        try:
            library = self.get_object()
            
            if library.owner != request.user and not UserLibraryRole.objects.filter(
                library=library, user=request.user, role='admin'
            ).exists():
                return Response({
                    'status': 'error',
                    'message': 'You do not have permission to modify this library.'
                }, status=403)
            
            library.is_active = not library.is_active
            library.save()
            
            status_text = 'activated' if library.is_active else 'deactivated'
            return Response({
                'status': 'success',
                'message': f'Library has been {status_text} successfully.',
                'is_active': library.is_active
            })
            
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=500)

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
            
            # Check if library uses custom content types
            if library.content_source != 'custom':
                return Response({
                    'status': 'error',
                    'message': 'This library does not use custom content types.'
                }, status=400)
            
            categories_data = request.data.get('categories', [])
            if not categories_data:
                return Response({
                    'status': 'error',
                    'message': 'No categories provided.'
                }, status=400)
            
            # Import here to avoid circular imports
            from videos.models import ContentType
            
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
                
                content_type = ContentType.objects.create(**category_kwargs)
                created_categories.append(content_type)
            
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
    """
    BACKEND/FRONTEND-READY: CRUD operations for user library roles.
    MAPPED TO: /api/roles/ endpoints
    USED BY: Library member management interface
    
    Manages user and admin role assignments within libraries.
    """
    queryset = UserLibraryRole.objects.all()
    serializer_class = UserLibraryRoleSerializer
    
    def get_permissions(self):
        """
        BACKEND-READY: Permission control for role management.
        MAPPED TO: DRF permission system
        USED BY: Role management endpoints
        
        Requires authentication for write operations.
        """
        write_actions = ['create', 'update', 'partial_update', 'destroy']
        permission_classes = [permissions.IsAuthenticated] if self.action in write_actions else [permissions.AllowAny]
        return [permission() for permission in permission_classes]

def process_base64_image(base64_data, name=None):
    """
    BACKEND-READY: Convert base64 image data to Django ContentFile.
    MAPPED TO: Image upload processing
    USED BY: EditLibraryView.post() for category images
    
    Processes base64 encoded images and creates proper Django file objects.
    """
    if ',' in base64_data:
        format, imgstr = base64_data.split(';base64,')
        ext = format.split('/')[-1]
    else:
        imgstr = base64_data
        ext = 'png'
    
    if not name:
        import uuid
        name = f"{uuid.uuid4()}.{ext}"
    elif not name.endswith(f'.{ext}'):
        name = f"{name}.{ext}"
    
    data = base64.b64decode(imgstr)
    return ContentFile(data, name=name)

class CreateLibraryView(LoginRequiredMixin, TemplateView):
    """
    BACKEND/FRONTEND-READY: Library creation interface.
    MAPPED TO: /admin/create-library/ URL
    USED BY: create_library_admin.html template
    
    Handles both GET (form display) and POST (form submission) for library creation.
    PERMISSIONS: Only users with Owner level (superuser) can create libraries.
    """
    template_name = 'create_library_admin.html'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Check if user has Owner level permissions before allowing access.
        """
        if not (request.user.is_superuser or request.user.role == 'owner'):
            messages.error(request, 'Only users with Owner level access can create libraries.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        try:
            # Get content source selection
            content_source = request.POST.get('content_source', 'custom')
            
            data = {
                'name': request.POST.get('name'),
                'description': request.POST.get('description'),
                'content_source': content_source,
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
                
                # Content types are automatically set up by Library.save() method
                
                # For custom libraries, handle any additional selected subject areas
                if content_source == 'custom':
                    # Get selected subject areas from checkboxes
                    custom_subject_areas = request.POST.getlist('custom_subject_areas')
                    
                    if custom_subject_areas:
                        from videos.models import ContentType
                        
                        # Create content types for each selected subject area
                        for subject_area in custom_subject_areas:
                            # Convert subject area code to display name
                            display_name = subject_area.replace('_', ' ').title()
                            
                            ContentType.objects.get_or_create(
                                subject_area=subject_area,
                                library=library,
                                defaults={
                                    'description': f'{display_name} content type for {library.name}',
                                    'is_active': True
                                }
                            )
                
                # Automatically assign default images to content types
                try:
                    from django.core.management import call_command
                    # Process all libraries to ensure consistency with deployment script
                    call_command('setup_content_type_images', force=True)
                except Exception as e:
                    # Log the error but don't fail the library creation
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Failed to assign content type images: {str(e)}")
                
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
    """
    BACKEND/FRONTEND-READY: Library management dashboard.
    MAPPED TO: /admin/manage-libraries/ URL  
    USED BY: manage_libraries.html template
    
    Displays user's owned libraries and libraries where they have user roles.
    """
    template_name = 'manage_libraries.html'
    
    def get_context_data(self, **kwargs):
        """
        BACKEND/FRONTEND-READY: Prepare library data for dashboard display.
        MAPPED TO: Template context
        USED BY: manage_libraries.html template
        
        Provides owned and contributed libraries for current user.
        """
        context = super().get_context_data(**kwargs)
        
        # Get all libraries the user can manage (owned + admin roles)
        user_libraries = Library.objects.filter(owner=self.request.user)
        admin_libraries = Library.objects.filter(
            user_roles__user=self.request.user,
            user_roles__role='admin'
        ).exclude(owner=self.request.user)
        
        # Combine and order by name
        all_libraries = list(user_libraries) + list(admin_libraries)
        all_libraries.sort(key=lambda x: x.name.lower())
        
        context['libraries'] = all_libraries
        
        # Add user role information for permission checking
        if self.request.user.is_superuser or self.request.user.role == 'owner':
            context['user_role'] = 'owner'
        else:
            context['user_role'] = 'user'  # Default role
        
        return context

class EditLibraryView(LoginRequiredMixin, TemplateView):
    """
    BACKEND/FRONTEND-READY: Library editing interface.
    MAPPED TO: /admin/edit-library/ URL
    USED BY: edit_library_admin.html template
    
    Comprehensive library editing with categories, users, and settings management.
    """
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
            if library.owner != self.request.user and not (self.request.user.is_superuser or self.request.user.role == 'owner'):
                context['permission_error'] = True
                context['library_name'] = library.name
                return context
            
            context['library'] = library
            
            # Get content types for this library - ALWAYS include all library content types (including Private)
            library_content_types = ContentType.objects.filter(library=library, is_active=True).order_by('subject_area')
            
            # Separate Private content type to show it first
            private_content_type = None
            other_content_types = []
            
            for content_type in library_content_types:
                if content_type.subject_area == 'private':
                    private_content_type = content_type
                else:
                    other_content_types.append(content_type)
            
            # Combine with Private first
            ordered_content_types = []
            if private_content_type:
                ordered_content_types.append(private_content_type)
            ordered_content_types.extend(other_content_types)
            
            context['content_types'] = ordered_content_types
            
            # Get users for this library
            context['users'] = UserLibraryRole.objects.filter(
                library=library,
                role='user'
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
            
            # Process content types
            if 'content_types' in request.POST:
                try:
                    content_types_data = json.loads(request.POST.get('content_types'))
                    
                    # Keep track of existing content type IDs
                    current_content_types = set(ContentType.objects.filter(library=library).values_list('id', flat=True))
                    processed_content_types = set()
                    
                    for content_type_data in content_types_data:
                        content_type_id = content_type_data.get('id')
                        
                        if content_type_id and not content_type_id.startswith('temp_'):
                            # Update existing content type
                            try:
                                content_type = ContentType.objects.get(id=content_type_id, library=library)
                                # Note: Content type name is now handled through subject_area enum
                                content_type.description = content_type_data.get('description', content_type.description)
                                
                                # Handle image if provided
                                if 'image' in content_type_data and content_type_data['image'] and content_type_data['image'].startswith('data:'):
                                    image_file = process_base64_image(
                                        content_type_data['image'],
                                        name=f"content_type_{content_type.display_name}"
                                    )
                                    content_type.image = image_file
                                    
                                content_type.save()
                                processed_content_types.add(int(content_type_id))
                                
                            except ContentType.DoesNotExist:
                                pass  # Content type might belong to another library or doesn't exist
                        else:
                            # Create new content type
                            new_content_type = ContentType(
                                subject_area=category_data.get('subject_area'),
                                description=category_data.get('description', ''),
                                library=library
                            )
                            new_content_type.save()
                            
                            # Handle image if provided
                            if 'image' in category_data and category_data['image'] and category_data['image'].startswith('data:'):
                                image_file = process_base64_image(
                                    category_data['image'],
                                    name=f"content_type_{new_content_type.display_name}"
                                )
                                new_content_type.image = image_file
                                new_content_type.save()
                                
                            processed_content_types.add(new_content_type.id)
                    
                    # Delete content types that were removed
                    content_types_to_delete = current_content_types - processed_content_types
                    if content_types_to_delete:
                        ContentType.objects.filter(id__in=content_types_to_delete, library=library).delete()
                        
                except json.JSONDecodeError:
                    return JsonResponse({
                        'status': 'error',
                        'message': "Invalid content type data format"
                    }, status=400, content_type='application/json')
            
            # Process users
            if 'users' in request.POST:
                try:
                    users_data = json.loads(request.POST.get('users'))
                    
                    # Keep track of existing user IDs
                    current_users = set(UserLibraryRole.objects.filter(
                        library=library, 
                        role='user'
                    ).values_list('id', flat=True))
                    
                    processed_users = set()
                    
                    for user_data in users_data:
                        user_id = user_data.get('id')
                        
                        if user_id and not user_id.startswith('temp_'):
                            # Existing user - just mark as processed
                            processed_users.add(int(user_id))
                        else:
                            # New user to add
                            from django.contrib.auth import get_user_model
                            User = get_user_model()
                            
                            # Try to find user by email
                            try:
                                user = User.objects.get(email=user_data.get('email'))
                                
                                # Check if user already has a role in this library
                                if not UserLibraryRole.objects.filter(library=library, user=user).exists():
                                    role = UserLibraryRole.objects.create(
                                        library=library,
                                        user=user,
                                        role='user'
                                    )
                                    processed_users.add(role.id)
                            except User.DoesNotExist:
                                # User doesn't exist - we might want to invite them
                                # For now, just log it
                                pass  # User not found
                    
                    # Remove users that were removed
                    users_to_delete = current_users - processed_users
                    if users_to_delete:
                        UserLibraryRole.objects.filter(id__in=users_to_delete, library=library).delete()
                        
                except json.JSONDecodeError:
                    return JsonResponse({
                        'status': 'error',
                        'message': "Invalid user data format"
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
