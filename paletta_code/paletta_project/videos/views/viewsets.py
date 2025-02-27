from rest_framework import viewsets, permissions
from ..models import Category, Video
from ..serializers import CategorySerializer, VideoSerializer
from rest_framework.decorators import action
from rest_framework.response import Response

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    
    def get_queryset(self):
        queryset = Video.objects.all()
        category_id = self.request.query_params.get('category', None)
        tag = self.request.query_params.get('tag', None)
        search = self.request.query_params.get('search', None)
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if tag:
            queryset = queryset.filter(tags__name=tag)
        if search:
            queryset = queryset.filter(title__icontains=search)
            
        return queryset
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        serializer.save(uploader=self.request.user) 