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
    Custom permission to only allow owners of an account or admins to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # write permissions are only allowed to the owner or admin
        return obj == request.user or request.user.role in ['admin', 'owner']

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
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
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get the current user's profile
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'], url_path='me/update')
    def update_profile(self, request):
        """
        Update the current user's profile
        """
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='me/change-password')
    def change_password(self, request):
        """
        Change the current user's password
        """
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        # check if the old password is correct
        if not user.check_password(old_password):
            return Response({'detail': 'Old password is incorrect.'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        # validate the new password
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({'detail': e.messages}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        # set the new password
        user.set_password(new_password)
        user.save()
        
        # update the token
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
    Check if a user exists and if they are already an admin or contributor.
    """
    # ONLY allow admin or owner users to access this endpoint
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
        
        # prepare response data
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
        
        # If library_id is provided, check if user is a contributor
        if library_id:
            try:
                library = Library.objects.get(id=library_id)
                is_contributor = UserLibraryRole.objects.filter(
                    user=user,
                    library=library,
                    role='contributor'
                ).exists()
                
                response_data['is_contributor'] = is_contributor
                
            except Library.DoesNotExist:
                pass
        
        return Response(response_data)
        
    except User.DoesNotExist:
        return Response({'exists': False})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def make_admin(request):
    """
    Promote a user to admin role.
    """
    # ONLY allow admin or owner users to access this endpoint
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
        
        # Check if user is an admin
        if user_to_promote.role in ['admin', 'owner']:
            return Response(
                {"success": False, "message": "User is already an administrator."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Promote user to admin
        user_to_promote.role = 'admin'
        user_to_promote.save()
        
        # Prepare admin data for response
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
    Revoke admin privileges from a user.
    """
    # ONLY allow admin or owner users to access this endpoint
    if request.user.role not in ['admin', 'owner']:
        return Response(
            {"detail": "You don't have permission to revoke admin privileges."},
            status=status.HTTP_403_FORBIDDEN
        )
        
    try:
        user_to_demote = User.objects.get(id=admin_id)
        
        # Check if user is an admin
        if user_to_demote.role != 'admin':
            return Response(
                {"success": False, "message": "User is not an administrator."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cannot demote yourself
        if user_to_demote == request.user:
            return Response(
                {"success": False, "message": "You cannot revoke your own admin privileges."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Demote user from admin to contributor
        user_to_demote.role = 'contributor'
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