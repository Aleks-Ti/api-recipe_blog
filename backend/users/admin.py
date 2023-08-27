from django.contrib import admin
from django.contrib.auth import admin as auth_admin

from users.models import Follow, User


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'date_joined',
    )
    list_filter = (
        'date_joined',
        'email',
        'first_name',
    )
    search_fields = (
        'email',
        'username',
        'first_name',
        'last_name',
    )


admin.site.register(Follow)
