from django.urls import include, path

from rest_framework.routers import DefaultRouter
from .views import (
    TagViewSet,
    RecipeViewSet,
    IngredientViewSet,
    CustomUserViewSet,
)

router = DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingridients')
router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
