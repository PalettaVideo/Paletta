"""
BACKEND/FRONTEND-READY: URL routing configuration for libraries app.
MAPPED TO: /api/libraries/ namespace
USED BY: Django URL dispatcher and API clients

Provides REST API endpoints for library and role management.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LibraryViewSet, UserLibraryRoleViewSet

router = DefaultRouter()
router.register('libraries', LibraryViewSet)
router.register('roles', UserLibraryRoleViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 