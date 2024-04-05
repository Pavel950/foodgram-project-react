from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, validators

import recipes.constants
from recipes.models import (
    Favorite,
    Follow,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCart,
    Tag,
    User
)


class NotNullBase64ImageField(Base64ImageField):
    def to_internal_value(self, data):
        if not isinstance(data, str) or not data.startswith('data:image'):
            raise serializers.ValidationError(
                {'errors': 'Что-то странное а не картинка.'}
            )
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
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
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and Follow.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        )


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
    amount = serializers.IntegerField(
        min_value=recipes.constants.MIN_POSITIVE_INTEGER,
        max_value=recipes.constants.MAX_DEFAULT
    )


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True, source='ingredient.id')
    name = serializers.CharField(read_only=True, source='ingredient.name')
    measurement_unit = serializers.CharField(
        read_only=True,
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeGetSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, required=True)
    image = NotNullBase64ImageField(
        required=True,
        allow_null=False,
        allow_empty_file=False
    )
    ingredients = IngredientRecipeSerializer(
        source='ingredient_in_recipe',
        many=True
    )
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)

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


class RecipeSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = NotNullBase64ImageField(
        required=True,
        allow_null=False,
        allow_empty_file=False
    )
    ingredients = IngredientRecipeShortSerializer(many=True)
    cooking_time = serializers.IntegerField(
        min_value=recipes.constants.MIN_POSITIVE_INTEGER,
        max_value=recipes.constants.MAX_COOKING_TIME
    )

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
        data_ingredients = data.get('ingredients', None)
        if not data_ingredients:
            raise serializers.ValidationError(
                {'errors': 'В списке отсутствуют ингредиенты.'}
            )
        if (
            data_ingredients and len(
                set(ingredient['id'] for ingredient in data_ingredients)
            ) != len(data_ingredients)
        ):
            raise serializers.ValidationError(
                {'errors': 'В списке есть повторяющиеся ингредиенты.'}
            )
        data_tags = data.get('tags', None)
        if not data_tags:
            raise serializers.ValidationError(
                {'errors': 'В списке отсутствуют теги.'}
            )
        if (len(data_tags) != len(set(data_tags))):
            raise serializers.ValidationError(
                {'errors': 'В списке есть повторяющиеся теги.'}
            )
        return data

    @staticmethod
    def add_ingredients_to_recipe(ingredients, recipe):
        ingredients_to_add = [
            IngredientRecipe(
                ingredient=ingredient.get('id'),
                recipe=recipe,
                amount=ingredient.get('amount')
            )
            for ingredient in ingredients
        ]
        IngredientRecipe.objects.bulk_create(ingredients_to_add)
        return recipe

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError(
                {'errors': 'Отсутствует запрос в контексте сериализатора.'}
            )
        recipe = Recipe.objects.create(**validated_data, author=request.user)
        recipe.tags.set(tags)
        return RecipeSerializer.add_ingredients_to_recipe(ingredients, recipe)

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.clear()
        instance.ingredients.clear()
        instance.tags.set(tags)
        RecipeSerializer.add_ingredients_to_recipe(ingredients, instance)
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


class UserRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError(
                {'errors': 'Отсутствует запрос в контексте сериализатора.'}
            )
        recipes_limit = request.query_params.get(
            'recipes_limit',
            None
        )
        qset = obj.recipes.all()
        if recipes_limit:
            try:
                int_recipes_limit = int(recipes_limit)
            except ValueError:
                raise serializers.ValidationError(
                    {'errors':
                     'Некорректное значение параметра recipes_limit.'}
                )
            qset = qset[:int_recipes_limit]
        return RecipeShortSerializer(qset, many=True).data


class UserRecipesCountSerializer(UserRecipesSerializer):
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserRecipesSerializer.Meta):
        pass

    def get_recipes_count(self, obj):
        return obj.recipes.all().count()


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        fields = '__all__'
        model = Favorite

        validators = (
            validators.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe')
            ),
        )


class ShoppingCartSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        fields = '__all__'
        model = ShoppingCart

        validators = (
            validators.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe')
            ),
        )


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        fields = '__all__'
        model = Follow

        validators = (
            validators.UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author')
            ),
        )

    def validate_author(self, value):
        if value == self.context['request'].user:
            raise serializers.ValidationError(
                'Пользователь не может подписаться на себя самого!'
            )
        return value
