from django_filters.rest_framework import filters, FilterSet

from recipes.models import Ingredient, Recipe, Tag, User


class IngredientFilter(FilterSet):
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.NumberFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        if not self.request.user.is_authenticated:
            return Recipe.objects.none()
        wanted_ids = [
            obj.id for obj in self.request.user.favorite_recipes.all()
        ]
        return queryset.filter(id__in=wanted_ids)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if not self.request.user.is_authenticated:
            return Recipe.objects.none()
        wanted_ids = [
            obj.id for obj in self.request.user.shopping_cart_recipes.all()
        ]
        return queryset.filter(id__in=wanted_ids)
