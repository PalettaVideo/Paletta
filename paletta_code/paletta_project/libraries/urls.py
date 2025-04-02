from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LibraryViewSet, UserLibraryRoleViewSet

router = DefaultRouter()
router.register('libraries', LibraryViewSet)
router.register('roles', UserLibraryRoleViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 