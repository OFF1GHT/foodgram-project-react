# Generated by Django 3.2.16 on 2023-09-23 12:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0011_alter_recipe_cooking_time'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recipeingredient',
            old_name='ingredients',
            new_name='ingredient',
        ),
    ]