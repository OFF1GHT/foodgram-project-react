from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from djoser.serializers import UserSerializer
from django.shortcuts import get_object_or_404

from api.fields import Base64ImageField
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
    ShoppingCart
)
from users.models import CustomUser, Subscribe
from recipes.constants import MIN_INGREDIENT_AMOUNT, COOKING_TIME


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

    recipe = ShortRecipeSerializer(read_only=True)
    user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )

    class Meta:
        model = Favorite
        fields = '__all__'

    def to_internal_value(self, data):
        recipe_id = data.get('recipe_id')
        user_id = data.get('user_id')

        if recipe_id is None or user_id is None:
            raise serializers.ValidationError(
                'Необходимо предоставить recipe_id и user_id'
            )

        recipe = get_object_or_404(Recipe, id=recipe_id)
        user = get_object_or_404(CustomUser, id=user_id)

        return {'recipe': recipe, 'user': user}

    def validate(self, data):
        user = data.get('user')
        recipe = data.get('recipe')

        if user.favorites.filter(recipe=recipe).exists():
            raise serializers.ValidationError(
                'Этот рецепт уже есть в избранном'
            )

        return data

    def to_representation(self, instance):
        return ShortRecipeSerializer(instance.recipe).data


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
        return (
            request
            and request.user.is_authenticated
            and obj.favorites.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and obj.shopping_list.filter(user=request.user).exists()
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

    def validate_cooking_time(self, value):
        if value <= COOKING_TIME:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше нуля.'
            )
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент.'
            )

        ingredient_ids = [ingredient['id'] for ingredient in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться'
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
        RecipeIngredient.objects.bulk_create(ingredients)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        request = self.context.get('request')
        author = validated_data.get(
            'author', request.user if request else None
        )
        recipe = Recipe.objects.create(author=author, **validated_data)
        self.add_ingredients(recipe, ingredients_data)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.add_ingredients(instance, ingredients)
        instance.tags.set(tags)
        return super().update(instance, validated_data)


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления и удаления рецептов из корзины покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('recipe', 'user')

    def to_internal_value(self, data):
        recipe_id = data.get('recipe_id')
        user_id = data.get('user_id')

        if recipe_id is None or user_id is None:
            raise serializers.ValidationError(
                'Необходимо предоставить recipe_id и user_id'
            )

        recipe = get_object_or_404(Recipe, id=recipe_id)
        user = get_object_or_404(CustomUser, id=user_id)

        return {'recipe': recipe, 'user': user}

    def validate(self, data):
        recipe = data.get('recipe')
        user = data.get('user')
        if user.shopping_list.filter(recipe=recipe).exists():
            raise serializers.ValidationError(
                'Этот рецепт уже есть в списке покупок'
            )
        return data


class SubscriptionSerializer(CustomUserSerializer):
    """Список подписок"""

    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.IntegerField(
        read_only=True, source='recipes.count'
    )

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit_recipes = request.query_params.get('recipes_limit')
        if limit_recipes is not None:
            recipes = obj.recipes.all()[:(int(limit_recipes))]
        else:
            recipes = obj.recipes.all()
        context = {'request': request}
        return ShortRecipeSerializer(recipes, many=True,
                                     context=context).data


class SubscribeSerializer(serializers.ModelSerializer):
    """Добавление и удаление подписок пользователя."""
    class Meta:
        model = Subscribe
        fields = ('author', 'user')

    def validate(self, data):
        user = data.get('user')
        author = data.get('author')
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя!'
            )

        if author.subscriber.filter(user=user).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на данного автора.'
            )
        return data
