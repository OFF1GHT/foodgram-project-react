import csv
from recipes.models import Ingredient

def import_ingredients_from_csv(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)
        for row in csv_reader:
            name, measurement_unit = row
            Ingredient.objects.create(name=name, measurement_unit=measurement_unit)
