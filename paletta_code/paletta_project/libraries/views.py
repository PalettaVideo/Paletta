from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
import json
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Library, LibraryMember
from .serializers import LibrarySerializer, LibraryMemberSerializer
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
        return obj.LibraryAdmin == request.user

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
        serializer.save(LibraryAdmin=self.request.user)
    
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
        if library.LibraryAdmin != request.user:
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
        if library.LibraryAdmin != request.user:
            return Response(
                {"detail": "Only the library administrator can add members."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'customer')
        
        if not user_id:
            return Response(
                {"detail": "User ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check if the user is already a member
        if LibraryMember.objects.filter(library=library, user_id=user_id).exists():
            return Response(
                {"detail": "User is already a member of this library."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Create the library member
        member = LibraryMember.objects.create(
            library=library,
            user_id=user_id,
            role=role
        )
        
        serializer = LibraryMemberSerializer(member)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class LibraryMemberViewSet(viewsets.ModelViewSet):
    queryset = LibraryMember.objects.all()
    serializer_class = LibraryMemberSerializer
    
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
                data['primary_color'] = primary_color
                
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
                # Save with LibraryAdmin set to the current user
                library = serializer.save(LibraryAdmin=request.user)
                
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
                            # Assign the first category by default
                            video.category = categories[0]
                            video.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Library created successfully.',
                    'redirect_url': 'manage_libraries'
                })
            else:
                print("Serializer errors:", serializer.errors)
                return JsonResponse({
                    'status': 'error',
                    'message': serializer.errors
                }, status=400)
        except Exception as e:
            import traceback
            print("Exception:", str(e))
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

class ManageLibrariesView(LoginRequiredMixin, TemplateView):
    template_name = 'manage_library_owner.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get libraries managed by the current user
        user_libraries = Library.objects.filter(LibraryAdmin=self.request.user)
        context['libraries'] = user_libraries
        
        print(f"User {self.request.user.username} has {user_libraries.count()} libraries")
        for lib in user_libraries:
            print(f" - {lib.name} (ID: {lib.id})")
            
        return context
        
    def get(self, request, *args, **kwargs):
        # Check if we need to store a library ID in session
        library_id = request.GET.get('set_library_id')
        if library_id:
            try:
                # Verify the library exists and user has permission
                library = Library.objects.get(id=library_id, LibraryAdmin=request.user)
                # Store in session
                request.session['editing_library_id'] = library_id
                request.session['editing_library_name'] = library.name  # Store the name for display
                # Redirect to the edit page
                return redirect('edit_library')
            except Library.DoesNotExist:
                messages.error(request, "Library not found or you don't have permission.")
                
        return super().get(request, *args, **kwargs)

class EditLibraryView(LoginRequiredMixin, TemplateView):
    """View for editing a library and its related data."""
    template_name = 'edit_library_admin.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        library_id = self.request.session.get('editing_library_id')
        
        if not library_id:
            context['error'] = "Library session expired. Please return to library management."
            return context
            
        # Add library name from session for page title even if we can't load the library
        library_name = self.request.session.get('editing_library_name', 'Unknown Library')
        context['library_name'] = library_name
        
        try:
            # Fetch the library by ID from session
            library = Library.objects.get(id=library_id)
            
            # Check if the current user is the library admin
            if library.LibraryAdmin != self.request.user:
                # If not, redirect to the libraries management page
                context['permission_error'] = True
                return context
            
            # Add library to context
            context['library'] = library
            
            # Fetch categories related to this library
            from videos.models import Category, Video
            
            # Method 1: Get categories from videos in this library
            videos_in_library = Video.objects.filter(libraries=library)
            category_ids_from_videos = videos_in_library.values_list('category', flat=True).distinct()
            
            # Get the categories from the unique category IDs
            # This will show existing categories that are actually in use
            categories = list(Category.objects.filter(id__in=category_ids_from_videos))
            
            # If no categories found, check if there are any categories in the database
            # This allows library admins to add categories even if no videos exist yet
            if not categories:
                # Get first 5 categories as examples they can use
                categories = list(Category.objects.all()[:5])
            
            context['categories'] = categories
            
            # Fetch contributors (library members with contributor role)
            context['contributors'] = LibraryMember.objects.filter(
                library=library, 
                role='contributor'
            )
            
            # Debug information
            print(f"Loaded library: {library.name} (ID: {library.id})")
            print(f"Library description: {library.description}")
            print(f"Library logo: {library.logo}")
            print(f"Categories count: {len(context['categories'])}")
            print(f"Contributors count: {len(context['contributors'])}")
            
        except Library.DoesNotExist:
            # Library not found
            context['library_not_found'] = True
            print(f"Library with ID {library_id} not found")
        except Exception as e:
            # Other error
            context['error'] = str(e)
            print(f"Error loading library data: {e}")
        
        return context
    
    def dispatch(self, request, *args, **kwargs):
        library_id = request.session.get('editing_library_id')
        
        if not library_id:
            messages.error(request, "Library session expired. Please return to library management.")
            return redirect('manage_libraries')
        
        try:
            # Check if the current user is the library admin
            library = Library.objects.get(id=library_id)
            if library.LibraryAdmin != request.user:
                # If not, redirect to the libraries management page
                messages.error(request, "You don't have permission to edit this library.")
                return redirect('manage_libraries')
        except Library.DoesNotExist:
            messages.error(request, "Library not found.")
            return redirect('manage_libraries')
        
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        print("="*80)
        print("EDIT LIBRARY POST REQUEST RECEIVED")
        print(f"Content-Type: {request.META.get('CONTENT_TYPE')}")
        print(f"X-Requested-With: {request.META.get('HTTP_X_REQUESTED_WITH')}")
        print(f"Request method: {request.method}")
        print("="*80)
        
        library_id = request.session.get('editing_library_id')
        
        if not library_id:
            print("No library_id in session")
            error_response = {
                'status': 'error',
                'message': 'Library session expired',
                'redirect_url': reverse('manage_libraries')
            }
            print(f"Error response: {error_response}")
            return JsonResponse(error_response, status=400)
        
        try:
            # Get the library by id from session
            library = Library.objects.get(id=library_id)
            
            # Check if the current user is the library admin
            if library.LibraryAdmin != request.user:
                return JsonResponse({
                    'status': 'error',
                    'message': "You don't have permission to edit this library."
                }, status=403)
            
            # Update basic library information
            library.name = request.POST.get('library_name', library.name)
            library.description = request.POST.get('description', library.description)
            
            # Handle logo upload
            if 'logo' in request.FILES:
                library.logo = request.FILES['logo']
            
            # Handle theme color
            if 'theme_color' in request.POST:
                library.primary_color = request.POST.get('theme_color')
            
            # Save the library
            library.save()
            
            # Process categories
            from videos.models import Category
            categories_json = request.POST.get('categories')
            new_categories = []
            
            if categories_json:
                try:
                    categories_data = json.loads(categories_json)
                    
                    # Create or update categories
                    for category_data in categories_data:
                        category_name = category_data.get('name')
                        category_desc = category_data.get('description')
                        
                        if not category_name:
                            continue
                            
                        # Try to find existing category or create a new one
                        try:
                            category = Category.objects.get(name=category_name)
                            # Update description if it has changed
                            if category.description != category_desc:
                                category.description = category_desc
                                category.save()
                        except Category.DoesNotExist:
                            # Create new category
                            category = Category.objects.create(
                                name=category_name,
                                description=category_desc
                            )
                        
                        # Add to our list of categories
                        new_categories.append(category)
                        
                        # Process category image if it's a new base64 image
                        if 'image' in category_data and category_data['image'].startswith('data:image'):
                            try:
                                image_file = process_base64_image(
                                    category_data['image'], 
                                    name=f"category_{category_name}"
                                )
                                category.image = image_file
                                category.save()
                            except Exception as e:
                                print(f"Error saving category image: {e}")
                                
                    # If we have videos in this library, ensure they're associated with categories
                    # For any videos without a category, assign them to the first category
                    if new_categories:
                        videos_without_category = library.videos.filter(category__isnull=True)
                        if videos_without_category.exists() and new_categories:
                            for video in videos_without_category:
                                video.category = new_categories[0]
                                video.save()
                                
                except json.JSONDecodeError:
                    print("Invalid JSON for categories")
            
            # Process contributors
            contributors_json = request.POST.get('contributors')
            if contributors_json:
                try:
                    contributors_data = json.loads(contributors_json)
                    
                    # Get current contributors
                    current_contributors = set(LibraryMember.objects.filter(
                        library=library, 
                        role='contributor'
                    ).values_list('user__email', flat=True))
                    
                    # Process new contributors
                    for contributor_data in contributors_data:
                        email = contributor_data.get('email')
                        
                        # Skip if already a contributor
                        if email in current_contributors:
                            current_contributors.remove(email)
                            continue
                            
                        # Try to find user with this email
                        from accounts.models import User
                        try:
                            user = User.objects.get(email=email)
                            
                            # Add as contributor if not already a member
                            if not LibraryMember.objects.filter(library=library, user=user).exists():
                                LibraryMember.objects.create(
                                    library=library,
                                    user=user,
                                    role='contributor'
                                )
                        except User.DoesNotExist:
                            # User not found - could implement invitation system here
                            print(f"User with email {email} not found")
                    
                    # Remove contributors that were deleted
                    if current_contributors:
                        LibraryMember.objects.filter(
                            library=library,
                            role='contributor',
                            user__email__in=current_contributors
                        ).delete()
                        
                except json.JSONDecodeError:
                    print("Invalid JSON for contributors")
            
            # Redirect to the libraries management page
            redirect_url = reverse('manage_libraries')
            print(f"Generated redirect URL: {redirect_url}")
            
            # Clear session after successful update
            if 'editing_library_id' in request.session:
                del request.session['editing_library_id']
            if 'editing_library_name' in request.session:
                del request.session['editing_library_name']
            
            # Check if this is a regular form submission (not AJAX)
            if request.POST.get('regular_submit') == 'true':
                messages.success(request, 'Library updated successfully')
                return redirect('manage_libraries')
            else:
                # AJAX response
                response_data = {
                    'status': 'success',
                    'message': 'Library updated successfully',
                    'redirect_url': redirect_url
                }
                print(f"Response data: {response_data}")
                
                # Ensure the response has the proper Content-Type
                response = JsonResponse(response_data)
                print("="*80)
                print("SENDING RESPONSE")
                print(f"Response Content-Type: {response['Content-Type']}")
                print(f"Response status code: {response.status_code}")
                print(f"Response content: {response.content}")
                print("="*80)
                
                return response
            
        except Library.DoesNotExist:
            error_response = {
                'status': 'error',
                'message': 'Library not found',
                'redirect_url': reverse('manage_libraries')
            }
            print(f"Error response: {error_response}")
            return JsonResponse(error_response, status=404)
        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"Error updating library: {error_msg}")
            print(traceback.format_exc())
            error_response = {
                'status': 'error',
                'message': error_msg,
                'redirect_url': reverse('manage_libraries')
            }
            print(f"Error response: {error_response}")
            return JsonResponse(error_response, status=500)
