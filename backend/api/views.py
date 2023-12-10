from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import Ingredient, Recipe, ShoppingCart, Tag
from users.models import CustomUser, Subscribe
from .filters import IngredientFilter, RecipeFilter
from .paginators import LimitPageNumberPaginator
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeReadSerializer,
                          ShoppingCartSerializer, SubscriptionSerializer,
                          TagSerializer, SubscribeSerializer)
from .utils import create_shopping_list_report

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
        return RecipeCreateSerializer

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            serializer = FavoriteSerializer(
                data={
                    'recipe': recipe.id,
                    'user': request.user.id
                }, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        favorite = request.user.favorites.filter(recipe=recipe)
        if not favorite:
            return Response(
                {'errors': 'Рецепт не добавлен в избранное'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
        serializer_class=ShoppingCartSerializer,
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = ShoppingCartSerializer(
            data={
                'recipe': recipe.id,
                'user': request.user.id
            }, context={'request': request}
        )
        if request.method == 'POST':
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        shopping_cart_item = get_object_or_404(
            ShoppingCart, user=request.user, recipe=recipe
        )
        serializer.delete(shopping_cart_item)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""
        shopping_cart_items = ShoppingCart.objects.filter(
            user=request.user
        ).values_list('recipe__name', flat=True)
        buy_list_text = create_shopping_list_report(shopping_cart_items)
        response = HttpResponse(buy_list_text, content_type="text/plain")
        response['Content-Disposition'] = (
            'attachment; filename=shopping-list.txt'
        )

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

    @action(detail=True,
            methods=('post', 'delete'),
            serializer_class=SubscribeSerializer,
            permission_classes=(IsAuthenticated,),
            )
    def subscribe(self, request, id=None):
        """Добавление и удаление подписок пользователя."""

        if request.method == 'POST':
            serializer = self.get_serializer(
                data=request.data,
                context={'request': request, 'id': id}
            )
            serializer.is_valid(raise_exception=True)
            response_data = serializer.save(id=id)
            return Response(
                {'message': 'Подписка успешно создана',
                 'data': response_data},
                status=status.HTTP_201_CREATED
            )
        subscription = get_object_or_404(
            Subscribe, user=self.request.user,
            author=get_object_or_404(CustomUser, id=id)
        )
        subscription.delete()
        return Response(
            {'Успешная отписка'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        methods=('get',),
        detail=False,
        serializer_class=SubscriptionSerializer,
        permission_classes=(IsAuthenticated,),
        pagination_class=LimitPageNumberPaginator,
    )
    def subscriptions(self, request):
        """Просмотр подписок пользователя."""

        paginated_users = self.paginate_queryset(
            User.objects.filter(
                id__in=Subscribe.objects.filter(
                    user=request.user
                ).values_list('author', flat=True)
            )
        )

        serializer = self.serializer_class(
            paginated_users, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
