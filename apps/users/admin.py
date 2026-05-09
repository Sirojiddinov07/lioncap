from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'preferred_currency', 'phone', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff', 'preferred_currency']
    search_fields = ['username', 'first_name', 'last_name', 'phone']

    fieldsets = UserAdmin.fieldsets + (
        ('Qo\'shimcha ma\'lumotlar', {
            'fields': ('role', 'preferred_currency', 'phone', 'address', 'passport'),
            'classes': ('wide',)
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Qo\'shimcha ma\'lumotlar', {
            'fields': ('role', 'preferred_currency', 'phone', 'address', 'passport'),
        }),
    )