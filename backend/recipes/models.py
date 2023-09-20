from django.db import models
from users.models import CustomUser
from django import forms

class Tag(models.Model):
    """Модель тег"""
    title = models.CharField(max_length=200)
    color = models.CharField(max_length=7, verbose_name='Цвет')
    slug = models.SlugField(max_length=200, unique=True)

    def __str__(self):
        return self.title
    

class Ingredient(models.Model):
    """Модель ингридиент"""
    name = models.CharField(max_length=200,  unique=True, default="")
    measurement_unit = models.CharField(max_length=200)


class Recipe(models.Model):
    """Модель рецепт"""
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='recipes/', null=True, blank=True)
    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='recipes'
    )
    text = models.TextField()
    ingredients = forms.ModelMultipleChoiceField(
        queryset=Ingredient.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
    )
    cooking_time = models.TimeField()

    def __str__(self):
        return self.title


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


class ShoppingList(models.Model):
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
    )


class RecipeIngredient(models.Model):
    """Модель связи рецепта и ингридиента"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
    )
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveBigIntegerField()

    def __str__(self):
        return f"{self.recipe.title} - {self.ingredients.title}"
