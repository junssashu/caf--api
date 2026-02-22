from django.contrib.auth import authenticate
from rest_framework import serializers

from accounts.models import User
from core.utils import phone_validator


class UserReadSerializer(serializers.ModelSerializer):
    isActive = serializers.BooleanField(source='is_active', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'nom', 'telephone', 'role', 'zone', 'isActive', 'createdAt']


class UserCreateSerializer(serializers.Serializer):
    nom = serializers.CharField(max_length=255)
    telephone = serializers.CharField(max_length=20)
    motDePasse = serializers.CharField(min_length=4, write_only=True)
    role = serializers.ChoiceField(choices=['admin', 'agent'])
    zone = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    isActive = serializers.BooleanField(default=True, required=False)

    def validate_telephone(self, value):
        phone_validator(value)
        if User.objects.filter(telephone=value).exists():
            from core.exceptions import ConflictError
            raise ConflictError('Ce numero de telephone est deja utilise.')
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            telephone=validated_data['telephone'],
            password=validated_data['motDePasse'],
            nom=validated_data['nom'],
            role=validated_data['role'],
            zone=validated_data.get('zone') or None,
            is_active=validated_data.get('isActive', True),
        )


class UserUpdateSerializer(serializers.Serializer):
    nom = serializers.CharField(max_length=255, required=False)
    telephone = serializers.CharField(max_length=20, required=False)
    motDePasse = serializers.CharField(min_length=4, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=['admin', 'agent'], required=False)
    zone = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    isActive = serializers.BooleanField(required=False)

    def validate_telephone(self, value):
        phone_validator(value)
        user = self.context.get('user')
        if user and User.objects.filter(telephone=value).exclude(id=user.id).exists():
            from core.exceptions import ConflictError
            raise ConflictError('Ce numero de telephone est deja utilise.')
        return value

    def update(self, user, validated_data):
        if 'nom' in validated_data:
            user.nom = validated_data['nom']
        if 'telephone' in validated_data:
            user.telephone = validated_data['telephone']
        if 'role' in validated_data:
            user.role = validated_data['role']
        if 'zone' in validated_data:
            user.zone = validated_data['zone'] or None
        if 'isActive' in validated_data:
            user.is_active = validated_data['isActive']

        mot_de_passe = validated_data.get('motDePasse', '')
        if mot_de_passe:
            user.set_password(mot_de_passe)

        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    telephone = serializers.CharField()
    motDePasse = serializers.CharField()
