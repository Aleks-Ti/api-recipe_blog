from django.db.models import Prefetch, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as django_filters
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from food.filter import IngredientSearchFilter, RecipeFilter
from food.models import (
    Cart,
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
)
from food.permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly
from food.serializers import (
    IngredientsSerializer,
    RecipeCreateSerializer,
    RecipeListSerializer,
    SimplifiedRecipeSerializer,
    TagSerializer,
)


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = [IsAdminOrReadOnly]


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeListSerializer
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = [IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return RecipeCreateSerializer
        return self.serializer_class

    @staticmethod
    def _relations(
        request: HttpResponse, instance: object, in_space: str, pk=None
    ):
        """Создание/разрыв связей между пользователем и объектами.

        Attrs:
            request - запрос пользователя.
            instance - экземляр класса по которому создать/оборвать связь.
            in_space - пространство в котором создается связь, пример:
                Карзина, Избранное.
                Текстовое представление для возврата human-readable
            pk - primary key/id - айди из url запроса для обращения.
        """
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            _, created = instance.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            serializer = SimplifiedRecipeSerializer(recipe)
            if not created:
                return Response(
                    {'errors': f'Уже есть в {in_space}.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        favorite = instance.objects.filter(user=request.user, recipe=recipe)
        if favorite.exists():
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'errors': f'Отсутствует в {in_space}.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
    )
    def favorite(self, request: HttpResponse, pk=None):
        """Добавление в избранное рецепта."""
        return self._relations(request, Favorite, 'Избранное', pk)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
    )
    def shopping_cart(self, request: HttpResponse, pk=None):
        """Добавление рецепта в карзину пользователя."""
        return self._relations(request, Cart, 'Карзина', pk)

    @action(
        detail=False,
        methods=['GET'],
    )
    def download_shopping_cart(self, request: HttpResponse):
        """Парс данных рецепта из карзины и скачивание данных пользователем."""
        cart_recipes = Cart.objects.filter(user=request.user).values_list(
            'recipe', flat=True
        )

        recipes_with_ingredients = (
            Recipe.objects.filter(pk__in=cart_recipes)
            .select_related('author')
            .prefetch_related(
                Prefetch(
                    'recipeingredient_set',
                    queryset=RecipeIngredient.objects.select_related(
                        'ingredient'
                    )
                    .annotate(total_amount=Sum('amount'))
                    .all(),
                    to_attr='ingredients_with_amounts',
                )
            )
        )

        response_text = ""
        for recipe in recipes_with_ingredients:
            response_text += f"Рецепт: {recipe.name}\n"
            count = 0
            for ingredient_with_amount in recipe.ingredients_with_amounts:
                count += 1
                ingredient = ingredient_with_amount.ingredient
                response_text += f"{count} * Ингредиент: {ingredient.name}"
                response_text += f": {ingredient_with_amount.total_amount}"
                response_text += f" {ingredient.measurement_unit}\n"

        response = HttpResponse(response_text, content_type='text/plain')
        response[
            'Content-Disposition'
        ] = 'attachment; filename="shopping_cart.txt"'
        return response
