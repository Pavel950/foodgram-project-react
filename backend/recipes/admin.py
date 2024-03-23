from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Ingredient, Recipe, Tag, IngredientRecipe, User

admin.site.register(Ingredient)
admin.site.register(IngredientRecipe)
admin.site.register(Recipe)
admin.site.register(Tag)
admin.site.register(User, UserAdmin)
