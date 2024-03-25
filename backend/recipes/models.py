from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    following = models.ManyToManyField(
        'self',
        verbose_name='Подписки',
        related_name='followers',
        symmetrical=False,
        blank=True
    )
    favorite_recipes = models.ManyToManyField(
        'Recipe',
        verbose_name='Избранные рецепты',
        related_name='recipe_followers',
        blank=True
    )
    shopping_cart_recipes = models.ManyToManyField(
        'Recipe',
        verbose_name='Рецепты в списке покупок',
        related_name='recipe_shoppers',
        blank=True
    )

    REQUIRED_FIELDS = ('first_name', 'last_name', 'email')


class Tag(models.Model):
    name = models.CharField('Название', max_length=200, unique=True)
    color = models.CharField('Цвет в HEX', max_length=7, unique=True)
    slug = models.SlugField('Slug', unique=True)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=200)
    measurement_unit = models.CharField('Единицы измерения', max_length=200)

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
        User, on_delete=models.CASCADE, related_name='recipes')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        verbose_name='Ингредиенты',
        related_name='recipes'
    )
    name = models.CharField('Название', max_length=200)
    image = models.ImageField(
        upload_to='recipes/images/',
        # blank=True,
        null=True,
        default=None
    )
    text = models.TextField()
    cooking_time = models.PositiveSmallIntegerField('Время приготовления')
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    def __str__(self):
        return self.name


class TagRecipe(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField('Количество')
