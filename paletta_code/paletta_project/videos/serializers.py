from rest_framework import serializers
from .models import Video, Category, Tag

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'description', 'created_at')

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name')

class VideoSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.ReadOnlyField(source='uploader.username')
    category_name = serializers.ReadOnlyField(source='category.name')
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Video
        fields = ('id', 'title', 'description', 'category', 'category_name',
                  'uploader', 'uploaded_by_username', 'upload_date', 'updated_at', 'tags')
        read_only_fields = ('uploader', 'upload_date', 'updated_at') 