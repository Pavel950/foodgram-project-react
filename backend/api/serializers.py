import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser import serializers as djoser_serializers
from rest_framework import serializers

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientRecipe,
    Recipe,
    Tag,
    TagRecipe,
    ShoppingCart
)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        else:
            raise serializers.ValidationError(
                'Что-то странное а не картинка.'
            )
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


class IngredientRecipeShortSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_id(self, obj):
        return obj.ingredient.id

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit


class RecipeGetSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, required=True)
    image = Base64ImageField()
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
        if not request_user.is_authenticated:
            return False
        return Favorite.objects.filter(user=request_user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request_user = self.context.get('request').user
        if not request_user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(
            user=request_user,
            recipe=obj
        ).exists()


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
    ingredients = IngredientRecipeShortSerializer(many=True)

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

    def validate(self, data):
        if not data.get('ingredients', None):
            raise serializers.ValidationError(
                'В списке отсутствуют ингредиенты.'
            )
        if (
            data['ingredients'] and len(
                set(ingredient['id'] for ingredient in data['ingredients'])
            ) != len(data['ingredients'])
        ):
            raise serializers.ValidationError(
                'В списке есть повторяющиеся ингредиенты.'
            )
        if not data.get('tags', None):
            raise serializers.ValidationError(
                'В списке отсутствуют теги.'
            )
        if (len(data['tags']) != len(set(data['tags']))):
            raise serializers.ValidationError(
                'В списке есть повторяющиеся теги.'
            )
        return data

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
            ingredient_obj = ingredient.get('id')
            IngredientRecipe.objects.create(
                ingredient=ingredient_obj,
                recipe=recipe,
                amount=ingredient.get('amount')
            )

        return recipe

    def update(self, instance, validated_data):
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
            ingredient_obj = ingredient.get('id')
            IngredientRecipe.objects.create(
                ingredient=ingredient_obj,
                recipe=instance,
                amount=ingredient.get('amount')
            )

        return super().update(instance, validated_data)

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
