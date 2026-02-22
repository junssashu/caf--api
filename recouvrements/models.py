import uuid

from django.db import models

from core.enums import CategorieProduit, MethodePaiement, RecouvrementStatus


class Recouvrement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)
    point_de_vente = models.ForeignKey(
        'pdv.PointDeVente', on_delete=models.CASCADE, related_name='recouvrements',
    )
    agent = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='recouvrements',
    )
    montant = models.IntegerField()
    taux_commission = models.DecimalField(max_digits=5, decimal_places=4)
    commission = models.IntegerField()
    methode_paiement = models.CharField(max_length=15, choices=MethodePaiement.choices)
    status = models.CharField(
        max_length=15, choices=RecouvrementStatus.choices, default=RecouvrementStatus.EN_ATTENTE,
    )
    reference = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    validated_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'recouvrements'
        indexes = [
            models.Index(fields=['point_de_vente']),
            models.Index(fields=['agent']),
            models.Index(fields=['status']),
            models.Index(fields=['methode_paiement']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} - {self.montant} FCFA'

    @property
    def articles_summary(self):
        lignes = self.lignes.all()
        noms = [l.nom_produit for l in lignes]
        count = len(noms)
        preview = ', '.join(noms[:2])
        if count <= 2:
            suffix = 's' if count > 1 else ''
            return f'{count} article{suffix} - {preview}'
        return f'{count} articles - {preview}, ...'


class LigneRecouvrement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recouvrement = models.ForeignKey(
        Recouvrement, on_delete=models.CASCADE, related_name='lignes',
    )
    nom_produit = models.CharField(max_length=255)
    categorie = models.CharField(max_length=15, choices=CategorieProduit.choices)
    prix_unitaire = models.IntegerField()
    quantite = models.IntegerField()
    sous_total = models.IntegerField()

    class Meta:
        db_table = 'lignes_recouvrement'
        indexes = [
            models.Index(fields=['recouvrement']),
            models.Index(fields=['categorie']),
        ]

    def __str__(self):
        return f'{self.nom_produit} x{self.quantite}'
