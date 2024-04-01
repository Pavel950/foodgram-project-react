from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models


class User(AbstractUser):
    REQUIRED_FIELDS = ('first_name', 'last_name', 'username')
    USERNAME_FIELD = 'email'
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    following = models.ManyToManyField(
        'self',
        through='Follow',
        verbose_name='Подписки',
        related_name='followers',
        symmetrical=False,
        blank=True
    )
    favorite_recipes = models.ManyToManyField(
        'Recipe',
        through='Favorite',
        verbose_name='Избранные рецепты',
        related_name='recipe_followers',
        blank=True
    )
    shopping_cart_recipes = models.ManyToManyField(
        'Recipe',
        through='ShoppingCart',
        verbose_name='Рецепты в списке покупок',
        related_name='recipe_shoppers',
        blank=True
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'


class Tag(models.Model):
    name = models.CharField('Название', max_length=200, unique=True)
    color = models.CharField('Цвет в HEX', max_length=7, unique=True)
    slug = models.SlugField('Slug', unique=True)

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=200)
    measurement_unit = models.CharField('Единицы измерения', max_length=200)

    class Meta:
        ordering = ('name',)
        verbose_name = 'ингредиент'
        verbose_name_plural = 'ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    tags = models.ManyToManyField(
        Tag,
        through='TagRecipe',
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
    name = models.CharField('Название', max_length=200)
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение',
    )
    text = models.TextField('Текст')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[MinValueValidator(1)]
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'рецепт'
        verbose_name_plural = 'рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'name'],
                name='unique_author_name_in_recipe'
            )
        ]

    def __str__(self):
        return self.name


class TagRecipe(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField('Количество')


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_recipe_in_shopping_cart'
            )
        ]


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_recipe_in_favorite'
            )
        ]


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follow_followed_to')
    following_to = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follow_followers')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following_to'],
                name='unique_user_following'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('following_to')),
                name='prevent_self_follow'
            )
        ]
