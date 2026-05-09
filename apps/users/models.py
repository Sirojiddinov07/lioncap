from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.constants import UserRole, CurrencyType
from apps.core.utils import phone_number_validator


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser
    """
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.MASTER,
        verbose_name='Rol'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[phone_number_validator],
        verbose_name='Telefon'
    )
    address = models.TextField(blank=True, verbose_name='Manzil')
    passport = models.CharField(max_length=20, blank=True, verbose_name='Passport')

    preferred_currency = models.CharField(
        max_length=3, choices=CurrencyType.choices,
        default=CurrencyType.UZS, verbose_name="Afzal valyuta"
    )

    # Override groups and permissions to avoid clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_groups',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_permissions',
        related_query_name='custom_user',
    )

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def is_staff_member(self):
        return self.role in [UserRole.ADMIN, UserRole.STAFF]

    @property
    def is_master(self):
        return self.role == UserRole.MASTER