from django.db.models import Sum

from recipes.models import RecipeIngredient


def create_shopping_list_report(shopping_cart):
    buy_list = (
        RecipeIngredient.objects.filter(
            recipe__in=shopping_cart.values('recipe_id')
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(amount=Sum('amount'))
    )
    buy_list_text = 'Foodgram\nСписок покупок:\n'
    for item in buy_list:
        name = item['ingredient__name']
        measurement_unit = item['ingredient__measurement_unit']
        amount = item['amount']
        buy_list_text += f'{name}, {amount} {measurement_unit}\n'
    return buy_list_text
