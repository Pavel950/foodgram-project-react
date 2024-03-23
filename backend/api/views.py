from django.http import JsonResponse
from djoser.views import UserViewSet
from django.shortcuts import get_object_or_404
from rest_framework import generics, views, viewsets
from rest_framework.pagination import PageNumberPagination

from .serializers import IngredientSerializer, RecipeSerializer, TagSerializer, RecipeGetSerializer, UserSerializer, UserRecipesSerializer
from recipes.models import Ingredient, Recipe, Tag, User


class CustomUserViewSet(UserViewSet):
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination


class SubscriptionsListAPIView(generics.ListAPIView):
    serializer_class = UserRecipesSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return self.request.user.following.all()


class SubscriptionPostDeleteAPIView(views.APIView):
    def post(self, request, user_id):
        following_user = get_object_or_404(User, id=user_id)
        if request.user in following_user.followers.all():
            pass
            #нельзя подписываться дважды!
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
            pass
            #нельзя удалить из подписок того, на кого не подписан
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


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    # serializer_class = RecipeSerializer
    pagination_class = PageNumberPagination
    http_method_names = ('delete', 'get', 'patch', 'post', 'head', 'options')

    def get_serializer_class(self):
        # return RecipeGetSerializer
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
