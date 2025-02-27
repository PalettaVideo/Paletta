from rest_framework import serializers
from .models import Library, LibraryMember
from videos.serializers import VideoSerializer

class LibrarySerializer(serializers.ModelSerializer):
    owner_username = serializers.ReadOnlyField(source='owner.username')
    videos = VideoSerializer(many=True, read_only=True)
    
    class Meta:
        model = Library
        fields = ('id', 'name', 'description', 'owner', 'owner_username', 
                  'videos', 'created_at', 'updated_at')
        read_only_fields = ('owner', 'created_at', 'updated_at')

class LibraryMemberSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    library_name = serializers.ReadOnlyField(source='library.name')
    
    class Meta:
        model = LibraryMember
        fields = ('id', 'library', 'library_name', 'user', 'username', 'role', 'added_at')
        read_only_fields = ('added_at',) 