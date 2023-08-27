from django.urls import include, path
from rest_framework import routers

from food.views import IngredientsViewSet, RecipeViewSet, TagViewSet

router = routers.DefaultRouter()
router.register('ingredients', IngredientsViewSet)
router.register('tags', TagViewSet)
router.register('recipes', RecipeViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
