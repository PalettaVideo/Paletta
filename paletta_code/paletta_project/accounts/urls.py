from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.api_views import UserViewSet, CustomAuthToken

router = DefaultRouter()
router.register('users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('token/', CustomAuthToken.as_view(), name='token_obtain'),
    path('register/', UserViewSet.as_view({'post': 'create'}), name='register'),
] 