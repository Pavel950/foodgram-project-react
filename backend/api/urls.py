from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import IngredientViewSet, RecipeViewSet, TagViewSet, SubscriptionsListAPIView, CustomUserViewSet, SubscriptionPostDeleteAPIView, FavoritePostDeleteAPIView

router = SimpleRouter()
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('users', CustomUserViewSet)

urlpatterns = [
    path('users/<int:user_id>/subscribe/', SubscriptionPostDeleteAPIView.as_view()),
    path('recipes/<int:recipe_id>/favorite/', FavoritePostDeleteAPIView.as_view()),
    # path('users/favorites/', FavoritesListAPIView.as_view()),
    path('users/subscriptions/', SubscriptionsListAPIView.as_view()),
    path('auth/', include('djoser.urls.authtoken')),
    # path('', include('djoser.urls')),
    path('', include(router.urls)),
]
