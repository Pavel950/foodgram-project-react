from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import generics, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .pagination import PageNumberLimitPagination
from .permissions import AuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeSerializer,
    RecipeShortSerializer,
    TagSerializer,
    RecipeGetSerializer,
    UserSerializer,
    UserRecipesSerializer
)
from recipes.models import Ingredient, IngredientRecipe, Recipe, Tag, User

ERROR_MESSAGES = {
    'favorite': {
        'does_not_exist': 'Рецепта с id={id} не существует.',
        'not_in': 'Рецепта с id={id} нет в избранном.',
        'add_twice': 'Рецепт с id={id} уже есть в избранном.'
    },
    'shopping_cart': {
        'does_not_exist': 'Рецепта с id={id} не существует.',
        'not_in': 'Рецепта с id={id} нет в корзине.',
        'add_twice': 'Рецепт с id={id} уже есть в корзине.'
    },
    'subscription': {
        'self_following': 'Нельзя подписаться на самого себя.',
        'not_in': 'Отсутствует подписка на пользователя с id={id}.',
        'add_twice': 'Повторная попытка подписаться на пользователя c id={id}.'
    }
}


class CustomUserViewSet(UserViewSet):
    """ViewSet для пользователей."""

    serializer_class = UserSerializer
    pagination_class = PageNumberLimitPagination

    @action(["get", "put", "patch", "delete"],
            detail=False,
            permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)


class BasePostDeleteUserSubscriptionAPIView(views.APIView):
    """
    Базовый класс для создания/удаления подписок пользователя
    на что-то/кого-то.
    """

    permission_classes = [IsAuthenticated]

    def post(
        self, request,
        obj_id, obj_class,
        related_name, obj_serializer,
        error_messages_dict
    ):
        try:
            obj = obj_class.objects.get(id=obj_id)
        except obj_class.DoesNotExist:
            return Response(
                {'errors': error_messages_dict['does_not_exist'].format(
                    id=obj_id
                )},
                status=status.HTTP_400_BAD_REQUEST
            )
        return self.post_obj(
            request, obj,
            related_name, obj_serializer,
            error_messages_dict
        )

    def post_obj(
        self, request,
        obj, related_name,
        obj_serializer, error_messages_dict
    ):
        if request.user in getattr(obj, related_name).all():
            return Response(
                {'errors': error_messages_dict['add_twice'].format(id=obj.id)},
                status=status.HTTP_400_BAD_REQUEST
            )
        getattr(obj, related_name).add(request.user)
        return JsonResponse(
            obj_serializer(
                obj,
                context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    def delete(
        self, request,
        obj_id, obj_class,
        related_name, obj_serializer,
        error_messages_dict
    ):
        obj = get_object_or_404(obj_class, id=obj_id)
        if request.user not in getattr(obj, related_name).all():
            return Response(
                {'errors': error_messages_dict['not_in'].format(id=obj_id)},
                status=status.HTTP_400_BAD_REQUEST
            )
        getattr(obj, related_name).remove(request.user)
        return JsonResponse(
            obj_serializer(
                obj,
                context={'request': request}
            ).data,
            status=status.HTTP_204_NO_CONTENT
        )


class FavoritePostDeleteAPIView(BasePostDeleteUserSubscriptionAPIView):
    """View-класс добавления/удаления рецепта из избранного."""

    def post(self, request, recipe_id):
        return super().post(
            request, recipe_id,
            Recipe, 'recipe_followers',
            RecipeShortSerializer, ERROR_MESSAGES['favorite']
        )

    def delete(self, request, recipe_id):
        return super().delete(
            request, recipe_id,
            Recipe, 'recipe_followers',
            RecipeShortSerializer, ERROR_MESSAGES['favorite']
        )


class ShoppingCartPostDeleteAPIView(BasePostDeleteUserSubscriptionAPIView):
    """View-класс добавления/удаления рецепта из корзины."""

    def post(self, request, recipe_id):
        return super().post(
            request, recipe_id,
            Recipe, 'recipe_shoppers',
            RecipeShortSerializer, ERROR_MESSAGES['shopping_cart']
        )

    def delete(self, request, recipe_id):
        return super().delete(
            request, recipe_id,
            Recipe, 'recipe_shoppers',
            RecipeShortSerializer, ERROR_MESSAGES['shopping_cart']
        )


class SubscriptionPostDeleteAPIView(BasePostDeleteUserSubscriptionAPIView):
    """View-класс добавления/удаления подписки на пользователя."""

    def post(self, request, user_id):
        following_user = get_object_or_404(User, id=user_id)
        if request.user == following_user:
            return Response(
                {'errors': ERROR_MESSAGES['subscription']['self_following']},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().post_obj(
            request, following_user,
            'followers', UserRecipesSerializer,
            ERROR_MESSAGES['subscription']
        )

    def delete(self, request, user_id):
        return super().delete(
            request, user_id,
            User, 'followers',
            UserRecipesSerializer, ERROR_MESSAGES['subscription']
        )


class SubscriptionsListAPIView(generics.ListAPIView):
    """View-класс для получения списка подписок пользователя."""

    serializer_class = UserRecipesSerializer
    pagination_class = PageNumberLimitPagination

    def get_queryset(self):
        return self.request.user.following.all()


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


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
