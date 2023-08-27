from django.http import HttpRequest
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from food.serializers import FollowSerializer
from users.models import Follow, User


class FollowUsers(UserViewSet):
    @action(detail=False, methods=['GET'])
    def subscriptions(self, request: HttpRequest):
        user = request.user
        queryset = Follow.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['POST'], url_path='subscribe')
    def subscribe(self, request: HttpRequest, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if user.username == author.username:
            return Response(
                {'errors': 'Самоподписка запрещена.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.follower.filter(author=author).exists():
            return Response(
                {'errors': 'Вы уже подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        queryset, _ = Follow.objects.get_or_create(author=author, user=user)
        serializer = FollowSerializer(queryset, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request: HttpRequest, id=None):
        get_object_or_404(
            Follow,
            user=request.user,
            author=get_object_or_404(User, id=id),
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
