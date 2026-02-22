import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from accounts.managers import UserManager
from core.enums import UserRole
from core.utils import phone_validator


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=255)
    telephone = models.CharField(
        max_length=20, unique=True, validators=[phone_validator],
    )
    role = models.CharField(max_length=10, choices=UserRole.choices)
    zone = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Remove default AbstractUser fields we don't use
    username = None
    email = None
    first_name = None
    last_name = None

    USERNAME_FIELD = 'telephone'
    REQUIRED_FIELDS = ['nom']

    objects = UserManager()

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f'{self.nom} ({self.telephone})'
