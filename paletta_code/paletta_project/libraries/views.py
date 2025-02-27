from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Library, LibraryMember
from .serializers import LibrarySerializer, LibraryMemberSerializer

# Create your views here.

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a library to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.owner == request.user

class LibraryViewSet(viewsets.ModelViewSet):
    queryset = Library.objects.all()
    serializer_class = LibrarySerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrReadOnly]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
        
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        library = self.get_object()
        
        # Only the owner can add members
        if library.owner != request.user:
            return Response(
                {"detail": "Only the library owner can add members."},
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
