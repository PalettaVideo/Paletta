from rest_framework import viewsets, status, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from ..models import User
from ..serializers import UserSerializer

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