from django.db import models
from users.models import CustomUser
from django.core.validators import RegexValidator, MinValueValidator
from api.constants import (
    MAX_NAME_LENGTH,
    MAX_COLOR_LENGTH,
    MAX_SLUG_LENGTH,
    MAX_MEASUREMENT_UNIT_LENGTH,
)


class Tag(models.Model):
    """Модель тег"""

    name = models.CharField(max_length=MAX_NAME_LENGTH)
    color = models.CharField(
        max_length=MAX_COLOR_LENGTH,
        validators=[
            RegexValidator(
                regex='^#[0-9a-fA-F]{6}$', message='Введите корректный цвет'
            )
        ],
        verbose_name='Цвет',
    )
    slug = models.SlugField(max_length=MAX_SLUG_LENGTH, unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингридиент"""

    name = models.CharField(
        max_length=MAX_NAME_LENGTH, unique=False, blank=False
    )
    measurement_unit = models.CharField(
        max_length=MAX_MEASUREMENT_UNIT_LENGTH, blank=False, unique=False
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепт"""

    name = models.CharField(max_length=MAX_NAME_LENGTH, blank=False)
    image = models.ImageField(upload_to='recipes/', null=True, blank=True)
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='recipes',
        blank=False,
    )
    text = models.TextField(
        blank=False,
    )
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
    cooking_time = models.PositiveSmallIntegerField(
        blank=False,
        validators=[MinValueValidator(1)],
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class Favorite(models.Model):
    """Модель избранне"""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
    )


class ShoppingCart(models.Model):
    """Модель список покупок"""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='shopping_list',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        null=True,
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_shopping_cart_item'
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
    amount = models.PositiveIntegerField(
        blank=False,
        validators=[MinValueValidator(1)],
    )

    class Meta:
        verbose_name = ('Ингредиент в рецепте',)
        verbose_name_plural = 'Ингредиенты в рецепте'
