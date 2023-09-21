from recipes.models import Tag, Ingredient, Recipe, Favorite, ShoppingCart
from users.models import Subscribe, CustomUser
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeCreateSerializer,
    CustomUserSerializer
)
from rest_framework.permissions import SAFE_METHODS
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from djoser.views import viewsets, UserViewSet
from .filters import IngredientFilter
from django_filters.rest_framework import DjangoFilterBackend

User = get_user_model()

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeCreateSerializer
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response({'detail': 'Рецепт уже есть в избранном.'}, status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.create(user=user, recipe=recipe)
        elif request.method == 'DELETE':
            Favorite.objects.filter(user=user, recipe=recipe).delete()
        serializer = RecipeReadSerializer(recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @api_view(['POST'])
    @permission_classes([IsAuthenticated])
    def add_to_shopping_cart(request, id):
        recipe = get_object_or_404(Recipe, id=id)
        user = request.user
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            return Response({'detail': 'Рецепт уже добавлен в список покупок.'}, status=status.HTTP_400_BAD_REQUEST)
        ShoppingCart.objects.create(user=user, recipe=recipe)
        serializer = RecipeReadSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @api_view(['DELETE'])
    @permission_classes([IsAuthenticated])
    def remove_from_shopping_cart(request, id):
        recipe = get_object_or_404(Recipe, id=id)
        user = request.user
        shopping_item = ShoppingCart.objects.filter(user=user, recipe=recipe)
        if not shopping_item.exists():
            return Response({'errors': 'Рецепт не найден в списке покупок.'}, status=status.HTTP_400_BAD_REQUEST)
        shopping_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    def download_shopping_cart_pdf(request):
        user = request.user
        shopping_list_data = ShoppingCart.objects.filter(user=user)

        if not shopping_list_data.exists():
            return Response({'detail': 'Список покупок пуст.'}, status=400)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.pdf"'

        pdf = canvas.Canvas(response, pagesize=letter)
        pdf.drawString(100, 750, "Shopping List")

        y = 700
        for item in shopping_list_data:
            pdf.drawString(100, y, f"{item.recipe.name}: {item.amount}")
            y -= 20

        pdf.showPage()
        pdf.save()

        return response


class CustomUserViewSet(UserViewSet):
    queryset = CustomUser.objects.all()

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, id=None):
        if request.method == 'POST':
            user = request.user
            author = self.get_object()
            Subscribe.objects.create(user=user, author=author)
            serializer = CustomUserSerializer(author,
                                              context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            user = request.user
            author = self.get_object()
            subscription = Subscribe.objects.filter(user=user, author=author)
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)