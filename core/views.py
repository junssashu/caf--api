from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import ConflictError
from core.models import Settings
from core.permissions import IsAdmin, IsAdminOrAgent
from core.serializers import (
    CommissionUpdateSerializer,
    ProfileUpdateSerializer,
    SettingsSerializer,
)
from core.utils import phone_validator


class SettingsView(APIView):
    permission_classes = [IsAdminOrAgent]

    @extend_schema(tags=['Settings'], summary='Obtenir les parametres', responses={200: SettingsSerializer})
    def get(self, request):
        settings = Settings.get()
        serializer = SettingsSerializer(settings)
        return Response(serializer.data)


class ProfileUpdateView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(tags=['Settings'], summary='Modifier le profil', request=ProfileUpdateSerializer)
    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        data = serializer.validated_data

        if 'nom' in data:
            user.nom = data['nom']

        if 'telephone' in data:
            phone_validator(data['telephone'])
            from accounts.models import User
            if User.objects.filter(telephone=data['telephone']).exclude(id=user.id).exists():
                raise ConflictError('Ce numero de telephone est deja utilise.')
            user.telephone = data['telephone']

        mot_de_passe = data.get('motDePasse', '')
        if mot_de_passe:
            user.set_password(mot_de_passe)

        user.save()

        from accounts.serializers import UserReadSerializer
        return Response(UserReadSerializer(user).data)


class CommissionUpdateView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(tags=['Settings'], summary='Modifier le taux de commission', request=CommissionUpdateSerializer, responses={200: SettingsSerializer})
    def patch(self, request):
        serializer = CommissionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        settings = Settings.get()
        settings.taux_commission = serializer.validated_data['tauxCommission']
        settings.save()

        return Response(SettingsSerializer(settings).data)
