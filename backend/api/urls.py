from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (
    CustomUserViewSet,
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
)

router = SimpleRouter()
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('users', CustomUserViewSet)

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
