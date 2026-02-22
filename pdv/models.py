import uuid

from django.db import models

from core.enums import PDVStatus
from core.utils import phone_validator


class PointDeVente(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=255)
    adresse = models.TextField(blank=True, null=True)
    ville = models.CharField(max_length=100, default='Abidjan')
    commune = models.CharField(max_length=100)
    proprietaire_nom = models.CharField(max_length=255)
    proprietaire_telephone = models.CharField(
        max_length=20, blank=True, null=True, validators=[phone_validator],
    )
    status = models.CharField(
        max_length=15, choices=PDVStatus.choices, default=PDVStatus.EN_ATTENTE,
    )
    agent = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='points_de_vente',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'points_de_vente'
        indexes = [
            models.Index(fields=['agent']),
            models.Index(fields=['status']),
            models.Index(fields=['commune']),
        ]

    def __str__(self):
        return f'{self.code} - {self.nom}'
