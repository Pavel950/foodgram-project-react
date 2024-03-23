from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from recipes.models import Ingredient, Recipe, Tag, IngredientRecipe, TagRecipe

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request_user = self.context.get('request').user
        return request_user in obj.followers.all()


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Ingredient


# class IngredientRecipeSerializer(serializers.ModelSerializer):
#     name = serializers.SerializerMethodField()
#     measurement_unit = serializers.SerializerMethodField()

#     class Meta:
#         fields = ('id', 'name', 'measurement_unit', 'amount')
#         model = Ingredient

#     # def get_name(self, obj):
#     #     return obj.name
#     #     # return obj.ingredient.name

#     # def get_measurement_unit(self, obj):
#     #     return obj.measurement_unit
#     #     # return obj.ingredient.measurement_unit
        
#     def get_amount(self, obj):



# class IngredientAmountField(serializers.RelatedField):
#     def to_representation(self, value):
#         representation = {
#             'id': value.ingredient.id,
#             'name': value.ingredient.name,
#             'measurement_unit': value.ingredient.measurement_unit,
#             'amount': value.amount
#         }
#         return representation
    
#     def to_internal_value(self, data):
#         ingredient_id = data.get('id')
#         amount = data.get('amount')
#         ingredient = get_object_or_404(Ingredient, id=ingredient_id)
#         ingredient_amount_obj, status = IngredientAmount.objects.get_or_create(
#             ingredient=ingredient,
#             amount=amount
#         )
#         ingredient_amount_obj.save()
#         return ingredient_amount_obj



# class IngredientAmountSerializer(serializers.ModelSerializer):

#     class Meta:
#         fields = ('id', 'name', 'measurement_unit', 'amount')
#         model = IngredientAmount


# class IngredientRecipeGetSerializer(serializers.ModelSerializer):
#     name = serializers.ReadOnlyField(source='ingredient.name')


#     class Meta:
#         model = Ingredient
#         fields = (
#             'id', 'name', 'measurement_unit', 'amount'
#         )
#         Ingredient, recipe

#     def get_amount(self, obj):
#         ingredient = 
#         ingredient_recipe_obj = get_object_or_404(
#             IngredientRecipe,
#             ingredient=obj,
#             recipe=
#         )


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Tag


class IngredientRecipeSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit


class RecipeGetSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    # ingredients = IngredientRecipeSerializer(source='IngredientRecipe_set', many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = fields
        model = Recipe

    def get_ingredients(self, obj):
        qset = IngredientRecipe.objects.filter(recipe=obj)
        return [IngredientRecipeSerializer(i).data for i in qset]

    def get_is_favorited(self, obj):
        # ToDo
        return True

    def get_is_in_shopping_cart(self, obj):
        # ToDo
        return True


# class IngredientRecipeToSerializer(serializers.ModelSerializer):

#     class Meta:
#         fields


class RecipeSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = serializers.ListField(write_only=True)

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            # 'is_favorited',
            # 'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        model = Recipe

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)

        for tag in tags:
            TagRecipe.objects.create(
                tag=tag,
                recipe=recipe
            )

        for ingredient in ingredients:
            ingredient_obj = get_object_or_404(Ingredient, id=ingredient.get('id'))
            IngredientRecipe.objects.create(
                ingredient=ingredient_obj,
                recipe=recipe,
                amount=ingredient.get('amount')
            )

        return recipe


class RecipeShortSerializer(serializers.ModelSerializer):

    class Meta:
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
        model = Recipe


class UserRecipesSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_is_subscribed(self, obj):
        request_user = self.context.get('request').user
        # return obj in request_user.following.objects
        return request_user in obj.followers.all()

    def get_recipes(self, obj):
        return RecipeShortSerializer(obj.recipes.all(), many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.all().count()
