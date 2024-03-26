from django.http import JsonResponse
from djoser.views import UserViewSet
from djoser.permissions import CurrentUserOrAdmin
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .pagination import PageNumberLimitPagination
from .permissions import AuthorOrReadOnly  # , RecipeAuthorOrReadOnly
from .serializers import IngredientSerializer, RecipeSerializer, RecipeShortSerializer, TagSerializer, RecipeGetSerializer, UserSerializer, UserRecipesSerializer
from recipes.models import Ingredient, Recipe, Tag, User


class CustomUserViewSet(UserViewSet):
    serializer_class = UserSerializer
    pagination_class = PageNumberLimitPagination

    @action(["get", "put", "patch", "delete"], detail=False, permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)


class SubscriptionsListAPIView(generics.ListAPIView):
    serializer_class = UserRecipesSerializer
    pagination_class = PageNumberLimitPagination

    def get_queryset(self):
        return self.request.user.following.all()


class FavoritePostDeleteAPIView(views.APIView):
    def post(self, request, recipe_id):
        # recipe = get_object_or_404(Recipe, id=recipe_id)
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return Response(
                {'errors': f'Рецепта с id={recipe_id} не существует.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        self.check_object_permissions(request, recipe)
        if request.user in recipe.recipe_followers.all():
            return Response(
                {'errors': f'Рецепт с id={recipe_id} уже есть в избранном.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe.recipe_followers.add(request.user)
        return JsonResponse(
            RecipeShortSerializer(
                recipe,
                context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, id=recipe_id)
        # try:
        #     recipe = Recipe.objects.get(id=recipe_id)
        # except Recipe.DoesNotExist:
        #     return Response(
        #         {'errors': f'Рецепта с id={recipe_id} не существует.'},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )
        self.check_object_permissions(request, recipe)
        if request.user not in recipe.recipe_followers.all():
            return Response(
                {'errors': f'Рецепта с id={recipe_id} нет в избранном, поэтому его нельзя оттуда удалить.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe.recipe_followers.remove(request.user)
        return JsonResponse(
            RecipeShortSerializer(
                recipe,
                context={'request': request}
            ).data,
            status=status.HTTP_204_NO_CONTENT
        )

    def get_permissions(self):
        # permissions = super().get_permissions()
        # permissions.append(AuthorOrReadOnly())
        permissions = (IsAuthenticated(),)
        return permissions


class ShoppingCartPostDeleteAPIView(views.APIView):
    def post(self, request, recipe_id):
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return Response(
                {'errors': f'Рецепта с id={recipe_id} не существует.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        self.check_object_permissions(request, recipe)
        if request.user in recipe.recipe_shoppers.all():
            return Response(
                {'errors': f'Рецепт с id={recipe_id} уже есть в корзине.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe.recipe_shoppers.add(request.user)
        return JsonResponse(
            RecipeShortSerializer(
                recipe,
                context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, id=recipe_id)
        # try:
        #     recipe = Recipe.objects.get(id=recipe_id)
        # except Recipe.DoesNotExist:
        #     return Response(
        #         {'errors': f'Рецепта с id={recipe_id} не существует.'},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )
        self.check_object_permissions(request, recipe)
        if request.user not in recipe.recipe_shoppers.all():
            return Response(
                {'errors': f'Рецепта с id={recipe_id} нет в корзине, поэтому его нельзя оттуда удалить.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe.recipe_shoppers.remove(request.user)
        return JsonResponse(
            RecipeShortSerializer(
                recipe,
                context={'request': request}
            ).data,
            status=status.HTTP_204_NO_CONTENT
        )

    def get_permissions(self):
        permissions = (IsAuthenticated(),)
        return permissions


class SubscriptionPostDeleteAPIView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        following_user = get_object_or_404(User, id=user_id)
        if request.user == following_user:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.user in following_user.followers.all():
            return Response(
                {'errors': f'Повторная попытка подписаться на пользователя {following_user.username}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        following_user.followers.add(request.user)
        return JsonResponse(
            UserRecipesSerializer(
                following_user,
                context={'request': request}
            ).data,
            status=201
        )

    def delete(self, request, user_id):
        following_user = get_object_or_404(User, id=user_id)
        if request.user not in following_user.followers.all():
            return Response(
                {'errors': f'Нельзя отписаться от пользователя {following_user.username} - подписка отсутствует.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        following_user.followers.remove(request.user)
        return JsonResponse(
            UserRecipesSerializer(
                following_user,
                context={'request': request}
            ).data,
            status=204
        )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    # serializer_class = RecipeSerializer
    pagination_class = PageNumberLimitPagination
    # permission_classes = (RecipeAuthorOrReadOnly,)
    permission_classes = (AuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    # filterset_fields = ('is_favorited',)
    http_method_names = ('delete', 'get', 'patch', 'post', 'head', 'options')

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
