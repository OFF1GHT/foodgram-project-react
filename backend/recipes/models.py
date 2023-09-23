from django.db import models
from users.models import CustomUser
from django import forms


class Tag(models.Model):
    """Модель тег"""
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=7, verbose_name='Цвет')
    slug = models.SlugField(max_length=200, unique=True)

    def __str__(self):
        return self.title
    

class Ingredient(models.Model):
    """Модель ингридиент"""
    name = models.CharField(max_length=200,  unique=False, blank=False)
    measurement_unit = models.CharField(max_length=200, blank=False, unique=False)

    def __str__(self):
        return self.name

class Recipe(models.Model):
    """Модель рецепт"""
    name = models.CharField(max_length=200, blank=False)
    image = models.ImageField(upload_to='recipes/', null=True, blank=True)
    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='recipes', blank=False,
    )
    text = models.TextField(blank=False,)
    ingredients = models.ManyToManyField(
        Ingredient,
        blank=False,
        related_name='recipes',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        blank=False,
    )
    cooking_time = models.PositiveSmallIntegerField(blank=False)
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class Favorite(models.Model):
    """ Модель избранне"""
    user = models.ForeignKey(
        CustomUser,
        on_delete = models.CASCADE,
        related_name = 'favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete = models.CASCADE,
        related_name = 'favorites',
    )


class ShoppingCart(models.Model):
    """Модель список покупок"""
    user = models.ForeignKey(
        CustomUser,
        on_delete = models.CASCADE,
        related_name = 'shopping_list',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete = models.CASCADE,
        related_name = 'shopping_list',
        null=True,
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart_item'
            )
        ]

class RecipeIngredient(models.Model):
    """Модель связи рецепта и ингредиента"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes',
    )
    amount = models.PositiveBigIntegerField(blank=False)

    class Meta:
        verbose_name = 'Ингредиент в рецепте',
        verbose_name_plural = 'Ингредиенты в рецепте'