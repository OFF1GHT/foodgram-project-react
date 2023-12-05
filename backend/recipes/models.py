from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models

from users.models import CustomUser

from .constants import (HEX_COLOR_REGEX, MAX_COLOR_LENGTH, MAX_COOKING_TIME,
                        MAX_MEASUREMENT_UNIT_LENGTH, MAX_NAME_LENGTH,
                        MAX_SLUG_LENGTH, MIN_COOKING_TIME, MIN_QUANTITY)


class Tag(models.Model):
    """Модель тег"""

    name = models.CharField(
        max_length=MAX_NAME_LENGTH, verbose_name='Название'
    )
    color = models.CharField(
        max_length=MAX_COLOR_LENGTH,
        validators=[
            RegexValidator(
                regex=HEX_COLOR_REGEX, message='Введите корректный цвет'
            )
        ],
        verbose_name='Цвет',
    )
    slug = models.SlugField(
        max_length=MAX_SLUG_LENGTH, unique=True, verbose_name='Slug'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингридиент"""

    name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        unique=False,
        blank=False,
        verbose_name='Название',
    )
    measurement_unit = models.CharField(
        max_length=MAX_MEASUREMENT_UNIT_LENGTH,
        blank=False,
        unique=False,
        verbose_name='Единица измерения',
    )

    class Meta:
        unique_together = ('name', 'measurement_unit')
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепт"""

    name = models.CharField(
        max_length=MAX_NAME_LENGTH, blank=False, verbose_name='Название'
    )
    image = models.ImageField(
        upload_to='recipes/', null=True, blank=True, verbose_name='Изображение'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    text = models.TextField(
        blank=False,
        verbose_name='Описание',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        blank=False,
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        blank=False,
        verbose_name='Теги',
    )
    cooking_time = models.PositiveSmallIntegerField(
        blank=False,
        validators=[
            MinValueValidator(MIN_COOKING_TIME),
            MaxValueValidator(MAX_COOKING_TIME),
        ],
        verbose_name='Время приготовления',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class Favorite(models.Model):
    """Модель избранное"""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'


class ShoppingCart(models.Model):
    """Модель список покупок"""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        null=True,
        verbose_name='Рецепт',
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
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveIntegerField(
        blank=False,
        validators=[MinValueValidator(MIN_QUANTITY)],
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = ('Ингредиент в рецепте',)
        verbose_name_plural = 'Ингредиенты в рецепте'
