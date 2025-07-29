from rest_framework import viewsets, status, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from ..models import User
from ..serializers import UserSerializer
from rest_framework.views import APIView
from libraries.models import UserLibraryRole, Library

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    BACKEND-READY: Custom permission for user account access control.
    MAPPED TO: User API endpoints
    USED BY: UserViewSet permission checking
    
    Allows read access to all, write access only to account owner or admin users.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user or request.user.role in ['admin', 'owner']

class CustomAuthToken(ObtainAuthToken):
    """
    BACKEND/FRONTEND-READY: Enhanced authentication token endpoint.
    MAPPED TO: POST /api/accounts/token/
    USED BY: login.js and authentication flows
    
    Provides token-based authentication with extended user data in response.
    """
    def post(self, request, *args, **kwargs):
        """
        BACKEND/FRONTEND-READY: Authenticate user and return token with user data.
        MAPPED TO: POST /api/accounts/token/
        USED BY: Frontend login forms and API clients
        
        Returns authentication token plus user profile data for frontend state.
        Required fields: email, password
        """
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role
        })

class UserViewSet(viewsets.ModelViewSet):
    """
    BACKEND/FRONTEND-READY: Complete CRUD operations for user management.
    MAPPED TO: /api/users/ endpoints
    USED BY: User registration, profile management, and admin operations
    
    Provides user account management with role-based permissions and profile actions.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        """
        BACKEND-READY: Dynamic permission assignment based on action.
        MAPPED TO: DRF permission system
        USED BY: All user API endpoints
        
        Sets appropriate permissions for different CRUD operations.
        """
        permission_map = {
            'create': [permissions.AllowAny],
            'update': [IsOwnerOrAdmin],
            'partial_update': [IsOwnerOrAdmin],
            'destroy': [IsOwnerOrAdmin],
        }
        permission_classes = permission_map.get(self.action, [permissions.IsAuthenticated])
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        BACKEND/FRONTEND-READY: Get current user's profile data.
        MAPPED TO: GET /api/users/me/
        USED BY: Profile pages and user context loading
        
        Returns authenticated user's complete profile information.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'], url_path='me/update')
    def update_profile(self, request):
        """
        BACKEND/FRONTEND-READY: Update current user's profile.
        MAPPED TO: PUT /api/users/me/update/
        USED BY: Profile edit forms and settings pages
        
        Updates authenticated user's profile with validation.
        """
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='me/change-password')
    def change_password(self, request):
        """
        BACKEND/FRONTEND-READY: Change current user's password.
        MAPPED TO: POST /api/users/me/change-password/
        USED BY: Password change forms and security settings
        
        Validates old password and sets new password with token refresh.
        Required fields: old_password, new_password
        """
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not user.check_password(old_password):
            return Response({'detail': 'Old password is incorrect.'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({'detail': e.messages}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        
        return Response({
            'detail': 'Password changed successfully.',
            'token': token.key
        })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def check_user(request):
    """
    BACKEND-READY: Check user existence and roles for admin operations.
    MAPPED TO: POST /api/accounts/check-user/
    USED BY: Admin management interfaces
    
    Validates user existence and current role status for admin operations.
    Required fields: email
    """
    if request.user.role not in ['admin', 'owner']:
        return Response(
            {"detail": "You don't have permission to check users."},
            status=status.HTTP_403_FORBIDDEN
        )
        
    email = request.data.get('email')
    library_id = request.data.get('library_id')
    
    if not email:
        return Response(
            {"detail": "Email is required."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
        
        user_data = {
            'id': user.id,
            'email': user.email,
            'name': f"{user.first_name} {user.last_name}" if user.first_name else None,
            'institution': user.institution or None,
        }
        
        response_data = {
            'exists': True,
            'user': user_data,
            'is_admin': user.role in ['admin', 'owner'],
        }
        
        if library_id:
            try:
                library = Library.objects.get(id=library_id)
                is_user = UserLibraryRole.objects.filter(
                    user=user,
                    library=library,
                    role='user'
                ).exists()
                
                response_data['is_user'] = is_user
                
            except Library.DoesNotExist:
                pass
        
        return Response(response_data)
        
    except User.DoesNotExist:
        return Response({'exists': False})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def make_admin(request):
    """
    BACKEND-READY: Promote user to administrator role.
    MAPPED TO: POST /api/accounts/make-admin/
    USED BY: Admin management interfaces
    
    Promotes user to admin role with validation.
    Required fields: user_id
    """
    if request.user.role not in ['admin', 'owner']:
        return Response(
            {"detail": "You don't have permission to promote users to admin."},
            status=status.HTTP_403_FORBIDDEN
        )
        
    user_id = request.data.get('user_id')
    
    if not user_id:
        return Response(
            {"detail": "User ID is required."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user_to_promote = User.objects.get(id=user_id)
        
        if user_to_promote.role in ['admin', 'owner']:
            return Response(
                {"success": False, "message": "User is already an administrator."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_to_promote.role = 'admin'
        user_to_promote.save()
        
        libraries = []
        user_libraries = UserLibraryRole.objects.filter(user=user_to_promote)
        for user_library in user_libraries:
            libraries.append(user_library.library.name)
        
        admin_data = {
            'id': user_to_promote.id,
            'email': user_to_promote.email,
            'name': f"{user_to_promote.first_name} {user_to_promote.last_name}" if user_to_promote.first_name else user_to_promote.email,
            'institution': user_to_promote.institution or None,
            'libraries': libraries
        }
        
        return Response({
            'success': True,
            'message': 'User promoted to administrator successfully.',
            'admin': admin_data
        })
        
    except User.DoesNotExist:
        return Response(
            {"success": False, "message": "User not found."},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def revoke_admin(request, admin_id):
    """
    BACKEND-READY: Revoke administrator privileges from user.
    MAPPED TO: POST /api/accounts/revoke-administrator/{id}/
    USED BY: Admin management interfaces
    
    Demotes admin user to user role with validation.
    """
    if request.user.role not in ['admin', 'owner']:
        return Response(
            {"detail": "You don't have permission to revoke admin privileges."},
            status=status.HTTP_403_FORBIDDEN
        )
        
    try:
        user_to_demote = User.objects.get(id=admin_id)
        
        if user_to_demote.role != 'admin':
            return Response(
                {"success": False, "message": "User is not an administrator."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if user_to_demote == request.user:
            return Response(
                {"success": False, "message": "You cannot revoke your own admin privileges."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_to_demote.role = 'user'
        user_to_demote.save()
        
        return Response({
            'success': True,
            'message': 'Admin privileges revoked successfully.'
        })
        
    except User.DoesNotExist:
        return Response(
            {"success": False, "message": "User not found."},
            status=status.HTTP_404_NOT_FOUND
        ) 