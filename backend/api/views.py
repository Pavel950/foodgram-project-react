from django.http import FileResponse, Http404, JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .pagination import PageNumberLimitPagination
from .permissions import AuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeGetSerializer,
    RecipeSerializer,
    RecipeShortSerializer,
    TagSerializer,
    UserSerializer,
    UserRecipesSerializer
)
from recipes.models import (
    Favorite,
    Follow,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCart,
    Tag
)


class CustomUserViewSet(UserViewSet):
    """ViewSet для пользователей."""

    serializer_class = UserSerializer
    pagination_class = PageNumberLimitPagination

    @action(['get', 'put', 'patch', 'delete'],
            detail=False,
            permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        following_user = self.get_object()
        if request.method == 'POST':
            if request.user == following_user:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Follow.objects.filter(
                user=request.user,
                following_to=following_user
            ).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на пользователя '
                               f'{following_user.username}.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Follow.objects.create(
                user=request.user,
                following_to=following_user
            )
            return JsonResponse(
                UserRecipesSerializer(
                    following_user,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )
        else:
            try:
                follow = Follow.objects.get(
                    user=request.user,
                    following_to=following_user
                )
            except Follow.DoesNotExist:
                return Response(
                    {'errors': 'Вы не были подписаны на пользователя '
                               f'{following_user.username}.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow.delete()
            return JsonResponse(
                UserRecipesSerializer(
                    following_user,
                    context={'request': request}
                ).data,
                status=status.HTTP_204_NO_CONTENT
            )

    @action(['get'],
            detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            request.user.following.all(),
            request
        )
        return paginator.get_paginated_response(UserRecipesSerializer(
            page,
            many=True,
            context={'request': request}
        ).data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов."""

    queryset = Recipe.objects.all()
    pagination_class = PageNumberLimitPagination
    permission_classes = (AuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ('delete', 'get', 'patch', 'post', 'head', 'options')

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False)
    def download_shopping_cart(self, request):
        shopping_cart = {}
        for recipe in request.user.shopping_cart_recipes.all():
            for ingredient in recipe.ingredients.all():
                ingredient_amount = IngredientRecipe.objects.get(
                    ingredient=ingredient,
                    recipe=recipe
                ).amount
                shopping_cart[
                    (ingredient.name, ingredient.measurement_unit)
                ] = shopping_cart.get(
                    (ingredient.name, ingredient.measurement_unit),
                    0
                ) + ingredient_amount
        with open('shopping_cart.txt', 'w') as f:
            print('Список покупок:', file=f)
            for key in shopping_cart:
                print(f'{key[0]} - {shopping_cart[key]} {key[1]}', file=f)
        return FileResponse(open('shopping_cart.txt', 'rb'))

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            try:
                recipe = self.get_object()
            except Http404:
                return Response(
                    {'errors': 'Рецепт не найден.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Favorite.objects.filter(
                user=request.user,
                recipe=recipe
            ).exists():
                return Response(
                    {'errors': f'Рецепт с названием {recipe.name} '
                               'уже есть в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=request.user, recipe=recipe)
            return JsonResponse(
                RecipeShortSerializer(recipe).data,
                status=status.HTTP_201_CREATED
            )
        else:
            recipe = self.get_object()
            try:
                recipe_in_favorite = Favorite.objects.get(
                    user=request.user,
                    recipe=recipe
                )
            except Favorite.DoesNotExist:
                return Response(
                    {'errors': f'Рецепта с названием {recipe.name} '
                               'нет в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            recipe_in_favorite.delete()
            return JsonResponse(
                RecipeShortSerializer(recipe).data,
                status=status.HTTP_204_NO_CONTENT
            )

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            try:
                recipe = self.get_object()
            except Http404:
                return Response(
                    {'errors': 'Рецепт не найден.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if ShoppingCart.objects.filter(
                user=request.user,
                recipe=recipe
            ).exists():
                return Response(
                    {'errors': f'Рецепт с названием {recipe.name} '
                               'уже есть в корзине.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            return JsonResponse(
                RecipeShortSerializer(recipe).data,
                status=status.HTTP_201_CREATED
            )
        else:
            recipe = self.get_object()
            try:
                recipe_in_shopping_cart = ShoppingCart.objects.get(
                    user=request.user,
                    recipe=recipe
                )
            except ShoppingCart.DoesNotExist:
                return Response(
                    {'errors': f'Рецепта с названием {recipe.name} '
                               'нет в корзине.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            recipe_in_shopping_cart.delete()
            return JsonResponse(
                RecipeShortSerializer(recipe).data,
                status=status.HTTP_204_NO_CONTENT
            )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
