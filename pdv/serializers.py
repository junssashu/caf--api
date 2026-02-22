from rest_framework import serializers

from pdv.models import PointDeVente


class PDVListSerializer(serializers.ModelSerializer):
    proprietaireNom = serializers.CharField(source='proprietaire_nom', read_only=True)
    proprietaireTelephone = serializers.CharField(source='proprietaire_telephone', read_only=True)
    agentId = serializers.UUIDField(source='agent_id', read_only=True)
    agentNom = serializers.CharField(source='agent.nom', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = PointDeVente
        fields = [
            'id', 'code', 'nom', 'adresse', 'ville', 'commune',
            'proprietaireNom', 'proprietaireTelephone', 'status',
            'agentId', 'agentNom', 'createdAt',
        ]


class PDVCreateSerializer(serializers.Serializer):
    nom = serializers.CharField(max_length=255)
    adresse = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    ville = serializers.CharField(max_length=100, default='Abidjan', required=False)
    commune = serializers.CharField(max_length=100)
    proprietaireNom = serializers.CharField(max_length=255)
    proprietaireTelephone = serializers.CharField(
        max_length=20, required=False, allow_blank=True, allow_null=True,
    )
    agentId = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(
        choices=['ACTIF', 'INACTIF', 'EN_ATTENTE'], required=False,
    )

    def validate_proprietaireTelephone(self, value):
        if value:
            from core.utils import phone_validator
            phone_validator(value)
        return value

    def validate_agentId(self, value):
        from accounts.models import User
        try:
            agent = User.objects.get(pk=value, role='agent')
        except User.DoesNotExist:
            raise serializers.ValidationError('Agent introuvable ou invalide.')
        if not agent.is_active:
            raise serializers.ValidationError("L'agent n'est pas actif.")
        return value


class PDVUpdateSerializer(serializers.Serializer):
    nom = serializers.CharField(max_length=255, required=False)
    adresse = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    ville = serializers.CharField(max_length=100, required=False)
    commune = serializers.CharField(max_length=100, required=False)
    proprietaireNom = serializers.CharField(max_length=255, required=False)
    proprietaireTelephone = serializers.CharField(
        max_length=20, required=False, allow_blank=True, allow_null=True,
    )
    agentId = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(
        choices=['ACTIF', 'INACTIF', 'EN_ATTENTE'], required=False,
    )

    def validate_proprietaireTelephone(self, value):
        if value:
            from core.utils import phone_validator
            phone_validator(value)
        return value

    def validate_agentId(self, value):
        from accounts.models import User
        try:
            agent = User.objects.get(pk=value, role='agent')
        except User.DoesNotExist:
            raise serializers.ValidationError('Agent introuvable ou invalide.')
        return value
