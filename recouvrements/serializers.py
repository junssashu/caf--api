from rest_framework import serializers

from recouvrements.models import LigneRecouvrement, Recouvrement


class LigneSerializer(serializers.ModelSerializer):
    nomProduit = serializers.CharField(source='nom_produit')
    prixUnitaire = serializers.IntegerField(source='prix_unitaire')
    sousTotal = serializers.IntegerField(source='sous_total', read_only=True)

    class Meta:
        model = LigneRecouvrement
        fields = ['id', 'nomProduit', 'categorie', 'prixUnitaire', 'quantite', 'sousTotal']


class RecouvrementListSerializer(serializers.ModelSerializer):
    pointDeVenteId = serializers.UUIDField(source='point_de_vente_id', read_only=True)
    pointDeVenteNom = serializers.CharField(source='point_de_vente.nom', read_only=True)
    pointDeVenteCode = serializers.CharField(source='point_de_vente.code', read_only=True)
    agentId = serializers.UUIDField(source='agent_id', read_only=True)
    agentNom = serializers.CharField(source='agent.nom', read_only=True)
    lignes = LigneSerializer(many=True, read_only=True)
    articlesSummary = serializers.CharField(source='articles_summary', read_only=True)
    tauxCommission = serializers.DecimalField(
        source='taux_commission', max_digits=5, decimal_places=4, read_only=True,
    )
    methodePaiement = serializers.CharField(source='methode_paiement', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    validatedAt = serializers.DateTimeField(source='validated_at', read_only=True)

    class Meta:
        model = Recouvrement
        fields = [
            'id', 'code', 'pointDeVenteId', 'pointDeVenteNom', 'pointDeVenteCode',
            'agentId', 'agentNom', 'lignes', 'articlesSummary',
            'montant', 'tauxCommission', 'commission',
            'methodePaiement', 'status', 'reference', 'notes',
            'createdAt', 'validatedAt',
        ]


class LigneCreateSerializer(serializers.Serializer):
    nomProduit = serializers.CharField(max_length=255)
    categorie = serializers.ChoiceField(
        choices=['BOISSONS', 'ALIMENTATION', 'HABILLEMENT', 'ELECTRONIQUE', 'AUTRE'],
    )
    prixUnitaire = serializers.IntegerField(min_value=1)
    quantite = serializers.IntegerField(min_value=1)


class RecouvrementCreateSerializer(serializers.Serializer):
    pointDeVenteId = serializers.UUIDField()
    lignes = LigneCreateSerializer(many=True, min_length=1)
    methodePaiement = serializers.ChoiceField(
        choices=['MTN_MOMO', 'ORANGE_MONEY', 'ESPECES'],
    )
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_lignes(self, value):
        if not value:
            raise serializers.ValidationError('Au moins une ligne est requise.')
        return value


class StatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['VALIDE', 'REJETE'])
