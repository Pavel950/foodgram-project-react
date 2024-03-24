from django_filters.rest_framework import filters, FilterSet

from recipes.models import Recipe, Tag, User


class RecipeFilter(FilterSet):
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.NumberFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        # return queryset.filter(author__favorite_recipes)  obj in self.request.user.favorite_recipes
        wanted_ids = [obj.id for obj in self.request.user.favorite_recipes.all()]
        return queryset.filter(id__in=wanted_ids)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        wanted_ids = [obj.id for obj in self.request.user.shopping_cart_recipes.all()]
        return queryset.filter(id__in=wanted_ids)
