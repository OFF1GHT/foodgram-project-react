from django.core.exceptions import ValidationError
from django.db import IntegrityError
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from api.fields import Base64ImageField
from recipes.models import Favorite, Ingredient, Recipe, RecipeIngredient, Tag
from users.models import CustomUser

from .constants import MIN_INGREDIENT_AMOUNT


class CustomUserSerializer(UserSerializer):
    """Сериалиатор для пользователей"""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )
        model = CustomUser

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли пользователь на автора."""
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and obj.subscribing.filter(user=request.user).exists()
        )


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов"""

    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов"""

    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['name'] = representation['name'].capitalize()
        return representation


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Серилизатор для краткого вывода рецептов."""

    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного"""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')

    def validate(self, data):
        recipe_id = self.context['recipe_id']
        user = self.context['request'].user
        if Favorite.objects.filter(user=user, recipe_id=recipe_id).exists():
            raise serializers.ValidationError(
                'Этот рецепт уже есть в избранном'
            )
        return data

    def save_to_favorites(self):
        user = self.context['request'].user
        recipe = self.instance
        Favorite.objects.create(user=user, recipe=recipe)

    def remove_from_favorites(self):
        user = self.context['request'].user
        recipe = self.instance
        Favorite.objects.filter(user=user, recipe=recipe).delete()


class RecipeIngredientGetSerializer(serializers.ModelSerializer):
    """Сериализатор для получения ингридиента в рецепте"""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для получения списка рецептов"""

    tags = TagSerializer(many=True)
    image = Base64ImageField()
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientGetSerializer(
        many=True, source='recipe_ingredients'
    )
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)

    class Meta:
        fields = (
            'id',
            'image',
            'author',
            'ingredients',
            'tags',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'text',
            'cooking_time',
        )
        model = Recipe

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and obj.favorites.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and obj.shopping_list.filter(
                user=request.user, recipe=obj
            ).exists()
        )


class AddIngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингредиентов в рецепт."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def validate_amount(self, value):
        """Проверяем, что количество ингредиента больше 0."""

        if value <= MIN_INGREDIENT_AMOUNT:
            raise ValidationError(
                'Количество ингредиента должно быть больше 0'
            )
        return value


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов"""

    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    ingredients = AddIngredientRecipeSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate_tags(self, data):
        if not data:
            raise serializers.ValidationError('Выберите хотя бы один тег')
        if len(data) != len(set(data)):
            raise serializers.ValidationError('Тэги не должны повторяться')
        return data

    def validate_cooking_time(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше нуля.'
            )
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент.'
            )
        return value

    def add_ingredients(self, recipe, ingredients_data):
        ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient_data['id'].id,
                amount=ingredient_data['amount'],
            )
            for ingredient_data in ingredients_data
        ]
        try:
            RecipeIngredient.objects.bulk_create(ingredients)
        except IntegrityError:
            pass

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        self.add_ingredients(recipe, ingredients_data)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', [])
        tags = validated_data.pop('tags')
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.add_ingredients(instance, ingredients)
        instance.tags.set(tags)
        return super().update(instance, validated_data)


class ShoppingCartSerializer(serializers.Serializer):
    """Сериализатор для добавления и удаления рецептов из корзины покупок."""

    def validate(self, data, obj):
        recipe_id = data.get('recipe_id')
        user = data.get('user')

        if obj.shopping_list.filter(user=user, recipe_id=recipe_id).exists():
            raise ValidationError('Этот рецепт уже есть в списке покупок')

        return data


class SubscriptionSerializer(CustomUserSerializer):
    """Список подписок"""

    email = serializers.ReadOnlyField()
    id = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    first_name = serializers.ReadOnlyField()
    last_name = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = ShortRecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.subscriber.filter(
                user=request.user, author=obj
            ).exists()
        return False
