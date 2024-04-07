from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (IngredientViewSet, RecipeViewSet, TagViewSet,
                    UserSubscriptionViewSet)

router = SimpleRouter()
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('users', UserSubscriptionViewSet)

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
