from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipes', '0002_auto_20230919_1833'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ShoppingList',
            new_name='ShoppingCart',
        ),
    ]
