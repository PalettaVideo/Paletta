from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LibraryViewSet, LibraryMemberViewSet

router = DefaultRouter()
router.register('libraries', LibraryViewSet)
router.register('members', LibraryMemberViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 