from django.db.models import Count, Exists, F, OuterRef
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import (Favorite, Follow, Ingredient, IngredientRecipe,
                            Recipe, ShoppingCart, Tag, User)

from .filters import IngredientFilter, RecipeFilter
from .pagination import PageNumberLimitPagination
from .permissions import AuthorOrReadOnly
from .serializers import (FavoriteSerializer, FollowSerializer,
                          IngredientSerializer, RecipeGetSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          TagSerializer, UserRecipesSerializer, UserSerializer)


class UserSubscriptionViewSet(UserViewSet):
    """ViewSet для пользователей."""

    serializer_class = UserSerializer
    pagination_class = PageNumberLimitPagination

    def get_queryset(self):
        return User.objects.annotate(recipes_count=Count('recipes'))

    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
        return super().get_permissions()

    @staticmethod
    def create_relation(serializer, request, id):
        relation_dict = {
            'user': request.user.id,
            'author': id
        }
        relation_serializer = serializer(
            data=relation_dict,
            context={'request': request}
        )
        relation_serializer.is_valid(raise_exception=True)
        relation_serializer.save()
        return Response(
            relation_serializer.data,
            status=status.HTTP_201_CREATED
        )

    @staticmethod
    def delete_relation(relation_class, request, id):
        relation = relation_class.objects.filter(
            user=request.user,
            author__id=id
        )
        if relation.exists():
            relation.first().delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': (f'Автора с id = {id} нет '
                        f'в таблице {relation_class.__name__}.')},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True,
            methods=('post',),
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, id=None):
        return UserSubscriptionViewSet.create_relation(
            FollowSerializer,
            request,
            id
        )

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        return UserSubscriptionViewSet.delete_relation(Follow, request, id)

    @action(detail=False,
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        qset = User.objects.filter(
            follow_followers__user=request.user
        ).annotate(recipes_count=Count('recipes'))
        return self.get_paginated_response(UserRecipesSerializer(
            self.paginate_queryset(qset),
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

    pagination_class = PageNumberLimitPagination
    permission_classes = (AuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ('delete', 'get', 'patch', 'post', 'head', 'options')

    def get_queryset(self):
        qset = Recipe.objects.select_related('author').prefetch_related(
            'tags',
            'ingredients'
        )
        if self.request.user.is_authenticated:
            qset = qset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user__id=self.request.user.id,
                        recipe__pk=OuterRef('pk')
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user__id=self.request.user.id,
                        recipe__pk=OuterRef('pk')
                    )
                )
            )
        return qset

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipeSerializer

    @staticmethod
    def create_ingredients_str(ingredients):
        shopping_cart = {}
        for ingredient in ingredients:
            key = (ingredient['name'], ingredient['measurement_unit'])
            shopping_cart[key] = (shopping_cart.get(key, 0)
                                  + ingredient['amount'])

        file_content_string = 'Список покупок:'
        for key in shopping_cart:
            file_content_string += ('\n' + f'{key[0]} - {shopping_cart[key]} '
                                    f'{key[1]}')
        return file_content_string

    @action(detail=False)
    def download_shopping_cart(self, request):
        ingredients = IngredientRecipe.objects.filter(
            recipe__shoppingcart_set__user=request.user
        ).values(
            'amount',
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit'),
        ).order_by('name')

        return FileResponse(RecipeViewSet.create_ingredients_str(ingredients),
                            as_attachment=True,
                            content_type='text/plain')

    @staticmethod
    def create_relation(serializer, request, pk):
        relation_dict = {
            'user': request.user.id,
            'recipe': pk
        }
        relation_serializer = serializer(data=relation_dict)
        relation_serializer.is_valid(raise_exception=True)
        relation_serializer.save()
        return Response(
            relation_serializer.data,
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
            {'errors': (f'Рецепта с id = {pk} нет '
                        f'в таблице {relation_class.__name__}.')},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True,
            methods=('post',),
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk=None):
        return RecipeViewSet.create_relation(FavoriteSerializer, request, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return RecipeViewSet.delete_relation(Favorite, request, pk)

    @action(detail=True,
            methods=('post',),
            permission_classes=(IsAuthenticated,))
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
