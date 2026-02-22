from django.db import models


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Administrateur'
    AGENT = 'agent', 'Agent'


class PDVStatus(models.TextChoices):
    ACTIF = 'ACTIF', 'Actif'
    INACTIF = 'INACTIF', 'Inactif'
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'


class RecouvrementStatus(models.TextChoices):
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'
    VALIDE = 'VALIDE', 'Valide'
    REJETE = 'REJETE', 'Rejete'


class MethodePaiement(models.TextChoices):
    MTN_MOMO = 'MTN_MOMO', 'MTN MoMo'
    ORANGE_MONEY = 'ORANGE_MONEY', 'Orange Money'
    ESPECES = 'ESPECES', 'Especes'


class CategorieProduit(models.TextChoices):
    BOISSONS = 'BOISSONS', 'Boissons'
    ALIMENTATION = 'ALIMENTATION', 'Alimentation'
    HABILLEMENT = 'HABILLEMENT', 'Habillement'
    ELECTRONIQUE = 'ELECTRONIQUE', 'Electronique'
    AUTRE = 'AUTRE', 'Autre'
