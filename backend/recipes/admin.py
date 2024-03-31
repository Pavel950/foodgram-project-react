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


class TagRecipeInline(RequiredInline):
    model = Recipe.tags.through
    verbose_name = 'тег рецепта'
    verbose_name_plural = 'теги рецепта'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [
        IngredientRecipeInline,
        TagRecipeInline
    ]
    list_display = ('name', 'author', 'favorited_count')
    list_filter = ('author', 'tags',)
    search_fields = ('name',)
    filter_horizontal = ('tags',)

    def favorited_count(self, obj):
        return User.favorite_recipes.through.objects.filter(recipe=obj).count()


admin.site.register(Tag)
admin.site.register(User, UserAdmin)
