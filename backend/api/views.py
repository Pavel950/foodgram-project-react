from io import StringIO

from django.db.models import Count, Exists, F, OuterRef
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
    FavoriteSerializer,
    IngredientSerializer,
    RecipeGetSerializer,
    RecipeSerializer,
    RecipeShortSerializer,
    ShoppingCartSerializer,
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
    Tag,
    User
)


class CustomUserViewSet(UserViewSet):
    """ViewSet для пользователей."""

    serializer_class = UserSerializer
    pagination_class = PageNumberLimitPagination

    def get_queryset(self):
        return User.objects.annotate(recipes_count=Count('recipes'))

    # @action(['get', 'put', 'patch', 'delete'],
    #         detail=False,
    #         permission_classes=[IsAuthenticated])
    # def me(self, request, *args, **kwargs):
    #     return super().me(request, *args, **kwargs)

    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
        return super().get_permissions()

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
        # paginator = self.pagination_class()
        # page = paginator.paginate_queryset(
        #     User.objects.filter(
        #         follow_followers__user=request.user
        #     ).annotate(recipes_count=Count('recipes')),
        #     request
        # )
        qset = User.objects.filter(
            follow_followers__user=request.user
        ).annotate(recipes_count=Count('recipes'))
        return self.get_paginated_response(UserRecipesSerializer(
            self.paginate_queryset(qset),
            many=True,
            context={'request': request}
        ).data)
        # return paginator.get_paginated_response(UserRecipesSerializer(
        #     page,
        #     many=True,
        #     context={'request': request}
        # ).data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов."""

    # queryset = Recipe.objects.all()
    pagination_class = PageNumberLimitPagination
    permission_classes = (AuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ('delete', 'get', 'patch', 'post', 'head', 'options')

    def get_queryset(self):
        user_id = -1
        if self.request.user.is_authenticated:
            user_id = self.request.user.id
        return Recipe.objects.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(
                    user__id=user_id,
                    recipe__pk=OuterRef('pk')
                )
            ),
            is_in_shopping_cart=Exists(
                ShoppingCart.objects.filter(
                    user__id=user_id,
                    recipe__pk=OuterRef('pk')
                )
            )
        )

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipeSerializer

    # def perform_create(self, serializer):
    #     serializer.save(author=self.request.user)

    @action(detail=False)
    def download_shopping_cart(self, request):
        ingredients = ShoppingCart.objects.filter(
            recipe__shopping__user=request.user
        ).values(
            name=F('recipe__ingredients__name'),
            amount=F('recipe__ingredients__ingredient_in_recipe__amount'),
            measurement_unit=F('recipe__ingredients__measurement_unit')
        ).order_by('name')

        shopping_cart = {}
        for ingredient in ingredients:
            key = (ingredient['name'], ingredient['measurement_unit'])
            shopping_cart[key] = (shopping_cart.get(key, 0)
                                  + ingredient['amount'])

        # print(shopping_cart)
        # for recipe in request.user.shopping_cart_recipes.all():
        #     for ingredient in recipe.ingredients.all():
        #         ingredient_amount = IngredientRecipe.objects.get(
        #             ingredient=ingredient,
        #             recipe=recipe
        #         ).amount
        #         shopping_cart[
        #             (ingredient.name, ingredient.measurement_unit)
        #         ] = shopping_cart.get(
        #             (ingredient.name, ingredient.measurement_unit),
        #             0
        #         ) + ingredient_amount
        file_content_string = 'Список покупок:'
        for key in shopping_cart:
            file_content_string += '\n' + f'{key[0]} - {shopping_cart[key]} {key[1]}'
        # with open('shopping_cart.txt', 'w') as f:
        #     print('Список покупок:', file=f)
        #     for key in shopping_cart:
        #         print(f'{key[0]} - {shopping_cart[key]} {key[1]}', file=f)
        # return FileResponse(open('shopping_cart.txt', 'rb'))
        return FileResponse(bytearray(file_content_string, 'utf-8'))

    @staticmethod
    def create_relation(serializer, request, pk):
        relation_dict = {
            'user': request.user.id,
            'recipe': pk
        }
        relation_serializer = serializer(data=relation_dict)  # context={'request': request}
        relation_serializer.is_valid(raise_exception=True)
        relation_instance = relation_serializer.save()
        return JsonResponse(
            RecipeShortSerializer(relation_instance.recipe).data,
            status=status.HTTP_201_CREATED
        )

    @staticmethod
    def delete_relation(relation_class, request, pk):
        relation = relation_class.objects.filter(
            user=request.user,
            recipe__id=pk
        )
        if relation.exists():
            relation.first().delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': f'Рецепта с id = {pk} нет в таблице {relation_class.__name__}.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True,
            methods=['post'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        return RecipeViewSet.create_relation(FavoriteSerializer, request, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return RecipeViewSet.delete_relation(Favorite, request, pk)

    @action(detail=True,
            methods=['post'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        return RecipeViewSet.create_relation(
            ShoppingCartSerializer,
            request,
            pk
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return RecipeViewSet.delete_relation(ShoppingCart, request, pk)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
