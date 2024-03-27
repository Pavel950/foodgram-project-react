from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (
    CustomUserViewSet,
    FavoritePostDeleteAPIView,
    IngredientViewSet,
    RecipeViewSet,
    ShoppingCartPostDeleteAPIView,
    SubscriptionPostDeleteAPIView,
    SubscriptionsListAPIView,
    TagViewSet,
)

router = SimpleRouter()
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('users', CustomUserViewSet)

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('recipes/<int:recipe_id>/favorite/',
         FavoritePostDeleteAPIView.as_view()),
    path('recipes/<int:recipe_id>/shopping_cart/',
         ShoppingCartPostDeleteAPIView.as_view()),
    path('users/<int:user_id>/subscribe/',
         SubscriptionPostDeleteAPIView.as_view()),
    path('users/subscriptions/', SubscriptionsListAPIView.as_view()),
    path('', include(router.urls)),
]
