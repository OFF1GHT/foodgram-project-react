from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from djoser.serializers import UserSerializer
from api.fields import Base64ImageField
from rest_framework.fields import SerializerMethodField
from django.db.models import F
from django.core.exceptions import ValidationError

from recipes.models import Tag, Ingredient, Recipe, Favorite, ShoppingCart, RecipeIngredient
from users.models import CustomUser, Subscribe


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        fields = '__all__'
        model = CustomUser

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли пользователь на автора."""
        request = self.context.get('request')
        if request.user.is_authenticated:
            return Subscribe.objects.filter(user=request.user, author=obj).exists()
        return False

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['name'] = representation['name'].capitalize()
        return representation


class RecipeCreateSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = IngredientSerializer(many=True)
    author = CustomUserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = '__all__'

    def validate_tags(self, data):
        if not data:
            raise serializers.ValidationError('Выберите хотя бы один тег')
        if len(data) != len(set(data)):
            raise serializers.ValidationError('Тэги не должны повторяться')
        return data

    def validate_ingredients(self, data):
        if not data:
            raise serializers.ValidationError('Список не может быть пустым')
        ingredient_ids = set()
        for ingredient in data:
            if ingredient['amount'] < 1:
                raise serializers.ValidationError('Количество ингридиентов должно быть больше нуля')
            ingredient_id = ingredient['id']
            if ingredient_id in ingredient_ids:
                raise serializers.ValidationError('Ингрдиенты не должны повторяться')
            ingredient_ids.add(ingredient_id)
        return data

    def create_ingredients(self, ingredients, recipe):
        recipe_ingredients = []
        for ingredient in ingredients:
            ingredient_id = ingredient.get('id')
            amount = ingredient.get('amount')
            if ingredient_id and amount >= 1:
                recipe_ingredients.append(
                    RecipeIngredient(recipe=recipe, ingredient_id=ingredient_id, amount=amount)
                )
        if recipe_ingredients:
            RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)
        if tags:
            recipe.tags.set(tags)
        if ingredients:
            self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags  = validated_data.pop('tags')
        if ingredients_data is not None:
            instance.ingredients.clear()
            self.create_ingredients(ingredients_data, instance)
        if tags is not None:
            instance.tags.set(tags)
        return super().update(instance, validated_data)


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    ingredients = IngredientSerializer(many=True)
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

    def get_ingredients(self, obj):
        recipe = obj
        ingredients = recipe.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('ingredientinrecipe__amount')
        )
        return ingredients

    def get_is_favorited(self, obj):
        request = self.context['request']
        if request and request.user.is_authenticated:
            is_favorited = Favorite.objects.filter(user=request.user, recipe=obj).exists()
            return is_favorited
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context['request']
        if request and request.user.is_authenticated:
            is_in_cart = ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()
            return is_in_cart
        return False


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def validate_amount(self, value):
        """Проверяем, что количество ингредиента больше 0."""

        if value <= 0:
            raise ValidationError(
                'Количество ингредиента должно быть больше 0'
            )
        return value


class AddIngredientRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для добавления ингредиентов в рецепт.
    """

    id = serializers.IntegerField(source='ingredient.id')
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def validate_amount(self, value):
        """Проверяем, что количество ингредиента больше 0."""

        if value <= 0:
            raise ValidationError(
                'Количество ингредиента должно быть больше 0'
            )
        return value

    def validate(self, attrs):
        """
        Проверяем, что ингредиент не добавлен уже в рецепт.
        """

        request = self.context.get('request')
        recipe_id = request.GET.get('recipe')
        ingredient_id = attrs['ingredient']['id']
        existing_ingredients = RecipeIngredient.objects.filter(
            recipe_id=recipe_id,
            ingredient_id=ingredient_id
        )
        if existing_ingredients.exists():
            raise ValidationError('Ингредиент уже добавлен в рецепт')
        return attrs
