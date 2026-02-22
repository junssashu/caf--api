from rest_framework import serializers

from core.models import Settings


class SettingsSerializer(serializers.ModelSerializer):
    tauxCommission = serializers.DecimalField(
        source='taux_commission', max_digits=5, decimal_places=2,
    )
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Settings
        fields = ['tauxCommission', 'updatedAt']


class ProfileUpdateSerializer(serializers.Serializer):
    nom = serializers.CharField(max_length=255, required=False)
    telephone = serializers.CharField(max_length=20, required=False)
    motDePasse = serializers.CharField(max_length=255, required=False, allow_blank=True)


class CommissionUpdateSerializer(serializers.Serializer):
    tauxCommission = serializers.DecimalField(max_digits=5, decimal_places=2)

    def validate_tauxCommission(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                'Le taux de commission doit etre entre 0 et 100.'
            )
        return value
