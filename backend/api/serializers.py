import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser import serializers as djoser_serializers
from rest_framework import serializers

from recipes.models import Ingredient, IngredientRecipe, Recipe, Tag, TagRecipe

RECIPE_CREATE_UPDATE_REQUIRED_FIELDS = (
    'tags',
    'ingredients',
    'name',
    'image',
    'text',
    'cooking_time'
)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class CustomUserCreateSerializer(djoser_serializers.UserCreateSerializer):

    class Meta(djoser_serializers.UserCreateSerializer.Meta):
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'password',
        )


class UserSerializer(djoser_serializers.UserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request_user = self.context.get('request').user
        return request_user in obj.followers.all()


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Ingredient


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
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        )
        read_only_fields = fields
        model = Recipe

    def get_ingredients(self, obj):
        qset = IngredientRecipe.objects.filter(recipe=obj)
        return [IngredientRecipeSerializer(i).data for i in qset]

    def get_is_favorited(self, obj):
        request_user = self.context.get('request').user
        # if not request_user.is_authenticated:
        #     return False
        return request_user in obj.recipe_followers.all()

    def get_is_in_shopping_cart(self, obj):
        request_user = self.context.get('request').user
        # if not request_user.is_authenticated:
        #     return False
        return request_user in obj.recipe_shoppers.all()


class RecipeSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()
    ingredients = serializers.ListField(write_only=True)

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        model = Recipe

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'Невозможно создать рецепт без указания тегов.'
            )
        tag_id_list = []
        for tag in tags:
            if tag.id in tag_id_list:
                raise serializers.ValidationError(
                    'Повторная попытка прикрепить тег к рецепту.'
                )
            tag_id_list.append(tag.id)
        return tags

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Невозможно создать рецепт без указания ингредиентов.'
            )
        ingredient_id_list = []
        for ingredient in ingredients:
            if 'id' not in ingredient:
                raise serializers.ValidationError(
                    'Не указан id ингредиента в рецепте.'
                )
            if 'amount' not in ingredient:
                raise serializers.ValidationError(
                    'Не указано количество ингредиента в рецепте.'
                )
            if int(ingredient['amount']) <= 0:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть положительным числом.'
                )
            if ingredient['id'] in ingredient_id_list:
                raise serializers.ValidationError(
                    'Повторная попытка добавить ингредиент в рецепт.'
                )
            if not Ingredient.objects.all().filter(id=ingredient['id']):
                raise serializers.ValidationError(
                    'Указанный ингредиент не найден в базе ингредиентов.'
                )
            ingredient_id_list.append(ingredient['id'])
        return ingredients

    def validate_cooking_time(self, cooking_time):
        if cooking_time <= 0:
            raise serializers.ValidationError(
                'Время приготовления должно быть положительным числом.'
            )
        return cooking_time

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
            ingredient_obj = get_object_or_404(
                Ingredient,
                id=ingredient.get('id')
            )
            IngredientRecipe.objects.create(
                ingredient=ingredient_obj,
                recipe=recipe,
                amount=ingredient.get('amount')
            )

        return recipe

    def update(self, instance, validated_data):
        for field_name in RECIPE_CREATE_UPDATE_REQUIRED_FIELDS:
            if field_name not in validated_data:
                raise serializers.ValidationError(
                    f'Не указано новое значения для поля {field_name} '
                    'при обновлении рецепта.'
                )

        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        instance.tags.clear()
        instance.ingredients.clear()

        for tag in tags:
            TagRecipe.objects.create(
                tag=tag,
                recipe=instance
            )

        for ingredient in ingredients:
            ingredient_obj = get_object_or_404(
                Ingredient,
                id=ingredient.get('id')
            )
            IngredientRecipe.objects.create(
                ingredient=ingredient_obj,
                recipe=instance,
                amount=ingredient.get('amount')
            )

        instance.name = validated_data.get('name')
        instance.image = validated_data.get('image')
        instance.text = validated_data.get('text')
        instance.cooking_time = validated_data.get('cooking_time')
        instance.save()
        return instance

    def to_representation(self, obj):
        return RecipeGetSerializer(obj, context=self.context).data


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
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, obj):
        request_user = self.context.get('request').user
        return request_user in obj.followers.all()

    def get_recipes(self, obj):
        recipes_limit = self.context.get('request').query_params.get(
            'recipes_limit',
            None
        )
        if recipes_limit:
            return RecipeShortSerializer(
                obj.recipes.all()[:int(recipes_limit)],
                many=True
                ).data
        return RecipeShortSerializer(obj.recipes.all(), many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.all().count()
