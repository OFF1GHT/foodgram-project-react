from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet

from recipes.models import Tag, Ingredient, Recipe, Favorite, ShoppingCart
from users.models import Subscribe, CustomUser
from .serializers import (
    TagSerializer, IngredientSerializer, RecipeReadSerializer,
    RecipeCreateSerializer, CustomUserSerializer, ShoppingCartSerializer,
    FavoriteSerializer, SubscriptionSerializer,
)
from .filters import IngredientFilter, RecipeFilter
from .utils import create_shopping_list_report
from .paginators import LimitPageNumberPaginator


User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        elif self.action == 'add_to_shopping_cart':
            return ShoppingCartSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        methods=('post', 'delete'),
        detail=True,
        serializer_class=FavoriteSerializer,
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = FavoriteSerializer(
            data={'recipe': recipe.id}, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        if request.method == 'POST':
            if Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                return Response(
                    {'detail': 'Рецепт уже есть в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        Favorite.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, id=pk)
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = ShoppingCartSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            recipe = ShoppingCart.objects.filter(
                user=request.user, recipe_id=pk
            )
            if recipe.exists():
                recipe.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""

        shopping_cart = ShoppingCart.objects.filter(user=request.user)
        buy_list_text = create_shopping_list_report(shopping_cart)
        response = HttpResponse(buy_list_text, content_type="text/plain")
        response[
            'Content-Disposition'
        ] = 'attachment; filename=shopping-list.txt'
        return response


class CustomUserViewSet(UserViewSet):
    queryset = CustomUser.objects.all()
    search_fields = ('username',)
    permission_classes = (AllowAny,)

    @action(
        methods=('get',),
        detail=False,
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request):
        """Информация о своем аккаунте."""

        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id=None):
        """Подписаться или отписаться."""
        user = request.user
        author = self.get_object()
        if request.method == 'POST':
            serializer = CustomUserSerializer(
                author, context={'request': request}
            )
            Subscribe.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            subscription = Subscribe.objects.filter(user=user, author=author)
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        methods=('get',),
        detail=False,
        serializer_class=SubscriptionSerializer,
        permission_classes=(IsAuthenticated,),
        pagination_class=LimitPageNumberPaginator,
    )
    def subscriptions(self, request):
        """Просмотр подписок пользователя."""
        user = request.user
        subscriptions = Subscribe.objects.filter(user=user).select_related(
            'author'
        )
        users = [subscription.author for subscription in subscriptions]
        paginated_users = self.paginate_queryset(users)
        serializer = self.serializer_class(
            paginated_users, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
