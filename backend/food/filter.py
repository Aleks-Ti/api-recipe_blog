from django_filters import rest_framework as django_filters
from rest_framework.filters import SearchFilter

from food.models import Cart, Favorite, Recipe, Tag


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )

    is_favorited = django_filters.BooleanFilter(
        method='filter_favorited',
        label='Favorite Recipe',
    )

    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_shopping_cart',
        label='Cart Recipe',
    )

    class Meta:
        model = Recipe
        fields = ['tags', 'is_favorited', 'author', 'is_in_shopping_cart']

    def filter_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and not user.is_anonymous:
            cart_recipes = Cart.objects.filter(user=self.request.user).values(
                'recipe'
            )
            return queryset.filter(id__in=cart_recipes)
        return queryset

    def filter_favorited(self, queryset, name, value):
        if value:
            cart_recipes = Favorite.objects.filter(
                user=self.request.user
            ).values('recipe')
            return queryset.filter(id__in=cart_recipes)
        return queryset


class IngredientSearchFilter(SearchFilter):
    search_param = 'name'
