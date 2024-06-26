from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Ingredient, IngredientRecipe, Recipe, Tag, User


class RequiredInline(admin.TabularInline):
    min_num = 1
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj=None, **kwargs)
        formset.validate_min = True
        return formset


class IngredientRecipeInline(RequiredInline):
    model = IngredientRecipe
    verbose_name = 'ингредиент в рецепте'
    verbose_name_plural = 'ингредиенты в рецепте'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (
        IngredientRecipeInline,
    )
    list_display = ('name', 'author', 'ingredients_list', 'favorited_count')
    list_filter = ('author', 'tags',)
    search_fields = ('name',)
    filter_horizontal = ('tags',)

    @admin.display(description='кол-во добавлений в избранное')
    def favorited_count(self, obj):
        return obj.favorite_set.count()

    @admin.display(description='ингредиенты')
    def ingredients_list(self, obj):
        return ', '.join(
            str(ingredient) for ingredient in obj.ingredients.all()
        )


admin.site.register(Tag)
admin.site.register(User, UserAdmin)
