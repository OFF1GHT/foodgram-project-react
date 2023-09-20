from django.contrib import admin
from .models import Recipe, Tag, Ingredient, Favorite, ShoppingList, RecipeIngredient

admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(Favorite)
admin.site.register(ShoppingList)
admin.site.register(RecipeIngredient)