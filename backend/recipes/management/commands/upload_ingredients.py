from csv import reader

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    """
    Добавить ингредиенты в БД:
    python manage.py upload_ingredients (локально)
    sudo docker-compose exec backend python manage.py upload_ingredients
    или
    sudo docker compose -f docker-compose.production.yml
    exec backend python manage.py upload_ingredients (для удаленного сервера)
    """

    def handle(self, *args, **kwargs):
        with open(
            'recipes/data/ingredients.csv', 'r', encoding='UTF-8'
        ) as ingredients:
            for row in reader(ingredients):
                if len(row) == 2:
                    Ingredient.objects.get_or_create(
                        name=row[0],
                        measurement_unit=row[1],
                    )
