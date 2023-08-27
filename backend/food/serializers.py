from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from food.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import Follow
from users.serializers import CustomUserSerializer


class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeListSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = RecipeIngredientsSerializer(
        source='recipeingredient_set',
        many=True,
        read_only=True,
    )
    image = serializers.ReadOnlyField(source='image.url')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Recipe.objects.filter(favorits__user=user, id=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Recipe.objects.filter(carts__user=user, id=obj.id).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = serializers.ListField(
        write_only=True, child=serializers.DictField()
    )
    image = Base64ImageField()

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

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                {'errors': 'Добавьте ингредиенты.'}
            )
        seen_ingredients = set()
        duplicate_ingredients = []

        for ingredient in value:
            ingredient_name = ingredient.get('id')
            if ingredient_name in seen_ingredients:
                duplicate_ingredients.append(ingredient_name)
            seen_ingredients.add(ingredient_name)

        if duplicate_ingredients:
            raise serializers.ValidationError(
                {'error': 'Повторяющиеся ингредиенты.'}
            )

        return value

    @staticmethod
    def _create_list_ingredients(recipe_instance, ingredients_data):
        """Добавление игредиентов к рецепту."""
        recipe_ingredients_list = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get('id')
            amount = ingredient_data.get('amount')
            try:
                amount = int(amount)
            except ValueError:
                raise serializers.ValidationError(
                    {'errors': 'Количество должно быть числом.'}
                )
            if amount < 0:
                raise serializers.ValidationError(
                    {'errors': 'Количество не может быть отрицательным.'}
                )
            recipe_ingredients_list.append(
                RecipeIngredient(
                    recipe=recipe_instance,
                    ingredient_id=ingredient_id,
                    amount=amount,
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients_list)

    @transaction.atomic
    def create(self, validated_data):
        tags_data = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)
        recipe = Recipe.objects.create(**validated_data)
        if tags_data is not None:
            recipe.tags.set(tags_data)

        self._create_list_ingredients(recipe, ingredients_data)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)

        instance = super().update(instance, validated_data)
        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            instance.ingredients.clear()
            self._create_list_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        context = {'request': self.context['request']}
        return RecipeListSerializer(instance, context=context).data


class SimplifiedRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='author.id')
    email = serializers.ReadOnlyField(source='author.email')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return Follow.objects.filter(user=user, author=obj.author).exists()

    def get_recipes(self, obj):
        recipes = obj.author.recipes.all()
        request = self.context['request']
        limit = request.GET.get('recipes_limit')
        if limit:
            recipes = recipes[: int(limit)]
        return SimplifiedRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()
