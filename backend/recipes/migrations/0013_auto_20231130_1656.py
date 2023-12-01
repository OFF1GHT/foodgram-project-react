# Generated by Django 3.2.16 on 2023-11-30 13:56

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0012_rename_ingredients_recipeingredient_ingredient'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingredient',
            options={
                'verbose_name': 'Ингредиент',
                'verbose_name_plural': 'Ингредиенты',
            },
        ),
        migrations.AlterModelOptions(
            name='tag',
            options={'verbose_name': 'Тег', 'verbose_name_plural': 'Теги'},
        ),
        migrations.AlterField(
            model_name='recipe',
            name='cooking_time',
            field=models.PositiveSmallIntegerField(
                validators=[django.core.validators.MinValueValidator(1)]
            ),
        ),
        migrations.AlterField(
            model_name='recipeingredient',
            name='amount',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='tag',
            name='color',
            field=models.CharField(
                max_length=7,
                validators=[
                    django.core.validators.RegexValidator(
                        message='Введите корректный цвет',
                        regex='^#[0-9a-fA-F]{6}$',
                    )
                ],
                verbose_name='Цвет',
            ),
        ),
    ]