from colorfield.fields import ColorField
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from . import constants


class User(AbstractUser):
    REQUIRED_FIELDS = ('first_name', 'last_name', 'username')
    USERNAME_FIELD = 'email'
    first_name = models.CharField(
        'Имя',
        max_length=constants.MAX_USER_FIELD_LENGTH
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=constants.MAX_USER_FIELD_LENGTH
    )
    email = models.EmailField(
        max_length=constants.MAX_EMAIL_LENGTH,
        unique=True
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'


class Tag(models.Model):
    name = models.CharField(
        'Название',
        max_length=constants.MAX_FIELD_LENGTH_DEFAULT,
        unique=True
    )
    color = ColorField('Цвет в HEX', unique=True)
    slug = models.SlugField(
        'Slug',
        max_length=constants.MAX_FIELD_LENGTH_DEFAULT,
        unique=True
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        'Название',
        max_length=constants.MAX_FIELD_LENGTH_DEFAULT
    )
    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=constants.MAX_FIELD_LENGTH_DEFAULT
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'ингредиент'
        verbose_name_plural = 'ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient_name_measurement_unit'
            ),
        )

    def __str__(self):
        return self.name


class Recipe(models.Model):
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        verbose_name='Ингредиенты',
        related_name='recipes'
    )
    name = models.CharField(
        'Название',
        max_length=constants.MAX_FIELD_LENGTH_DEFAULT
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение',
    )
    text = models.TextField('Текст')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=(
            MinValueValidator(constants.MIN_POSITIVE_INTEGER),
            MaxValueValidator(constants.MAX_COOKING_TIME)
        )
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'рецепт'
        verbose_name_plural = 'рецепты'
        constraints = (
            models.UniqueConstraint(
                fields=('author', 'name'),
                name='unique_author_name_in_recipe'
            ),
        )

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipe',
        verbose_name='Ингредиент'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipe',
        verbose_name='Рецепт'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=(
            MinValueValidator(constants.MIN_POSITIVE_INTEGER),
            MaxValueValidator(constants.MAX_DEFAULT)
        )
    )

    class Meta:
        verbose_name = 'ингредиент в рецепте'
        verbose_name_plural = 'ингредиенты в рецептах'
        constraints = (
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='unique_ingredient_in_recipe'
            ),
        )

    def __str__(self):
        return (f'ингредиент {self.ingredient.name} '
                f'в рецепте {self.recipe.name}')


class UserRecipeBaseModel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True


class ShoppingCart(UserRecipeBaseModel):

    class Meta:
        verbose_name = 'рецепт в корзине пользователя'
        verbose_name_plural = 'рецепты в корзинах пользователей'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_recipe_in_shopping_cart'
            ),
        )

    def __str__(self):
        return (f'рецепт {self.recipe.name} '
                f'в корзине пользователя {self.user.username}')


class Favorite(UserRecipeBaseModel):

    class Meta:
        verbose_name = 'рецепт в избранном пользователя'
        verbose_name_plural = 'рецепты в избранном пользователей'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_recipe_in_favorite'
            ),
        )

    def __str__(self):
        return (f'рецепт {self.recipe.name} '
                f'в избранном пользователя {self.user.username}')


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follow_followed_to',
        verbose_name='Пользователь'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follow_followers',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'подписка пользователя'
        verbose_name_plural = 'подписки пользователей'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_user_following'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_follow'
            )
        )

    def __str__(self):
        return (f'подписка пользователя {self.user.username} '
                f'на автора {self.author.username}')
