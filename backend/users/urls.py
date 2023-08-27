from django.urls import include, path
from rest_framework import routers

from users.views import FollowUsers

router = routers.DefaultRouter()
router.register('users', FollowUsers)

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
