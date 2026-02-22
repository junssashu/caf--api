from django.db.models import Count, Q, Sum
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from accounts.serializers import (
    LoginSerializer,
    UserCreateSerializer,
    UserReadSerializer,
    UserUpdateSerializer,
)
from core.pagination import CAFPagination
from core.permissions import IsAdmin


# --- Schema helpers ---
class _LoginResponseSerializer(drf_serializers.Serializer):
    user = UserReadSerializer()
    token = drf_serializers.CharField()


class _MessageSerializer(drf_serializers.Serializer):
    message = drf_serializers.CharField()


@extend_schema(tags=['Auth'])
class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={200: _LoginResponseSerializer},
        summary='Connexion',
        description='Authentification par telephone et mot de passe. Retourne un JWT.',
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        telephone = serializer.validated_data['telephone']
        mot_de_passe = serializer.validated_data['motDePasse']

        try:
            user = User.objects.get(telephone=telephone)
        except User.DoesNotExist:
            return Response(
                {'error': {'code': 'UNAUTHORIZED', 'message': 'Identifiants invalides'}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(mot_de_passe):
            return Response(
                {'error': {'code': 'UNAUTHORIZED', 'message': 'Identifiants invalides'}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {'error': {'code': 'FORBIDDEN', 'message': 'Compte desactive'}},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)
        refresh['role'] = user.role

        return Response({
            'user': UserReadSerializer(user).data,
            'token': str(refresh.access_token),
        })


@extend_schema(tags=['Auth'])
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={200: _MessageSerializer},
        summary='Deconnexion',
    )
    def post(self, request):
        return Response({'message': 'Deconnexion reussie'})


@extend_schema_view(
    list=extend_schema(
        tags=['Users'], summary='Lister les utilisateurs',
        parameters=[
            OpenApiParameter('role', str, description='Filtrer par role (admin/agent)'),
            OpenApiParameter('isActive', str, description='Filtrer par statut actif (true/false)'),
            OpenApiParameter('search', str, description='Recherche par nom ou telephone'),
        ],
    ),
    retrieve=extend_schema(tags=['Users'], summary='Detail utilisateur'),
    create=extend_schema(tags=['Users'], summary='Creer un utilisateur', request=UserCreateSerializer, responses={201: UserReadSerializer}),
    partial_update=extend_schema(tags=['Users'], summary='Modifier un utilisateur', request=UserUpdateSerializer, responses={200: UserReadSerializer}),
    destroy=extend_schema(tags=['Users'], summary='Desactiver un utilisateur', responses={200: _MessageSerializer}),
)
class UserViewSet(ViewSet):
    permission_classes = [IsAdmin]

    def list(self, request):
        qs = User.objects.all().order_by('-created_at')

        role = request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)

        is_active = request.query_params.get('isActive')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ('true', '1'))

        search = request.query_params.get('search')
        if search:
            qs = qs.filter(Q(nom__icontains=search) | Q(telephone__icontains=search))

        paginator = CAFPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = UserReadSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
        except (User.DoesNotExist, ValueError):
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': 'Utilisateur introuvable'}},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = UserReadSerializer(user).data

        from recouvrements.models import Recouvrement
        rec_stats = Recouvrement.objects.filter(agent_id=user.id).aggregate(
            totalRecouvrements=Count('id'),
            montantTotal=Sum('montant'),
            commissionTotale=Sum('commission'),
        )
        from pdv.models import PointDeVente
        total_pdv = PointDeVente.objects.filter(agent_id=user.id).count()

        data['stats'] = {
            'totalRecouvrements': rec_stats['totalRecouvrements'] or 0,
            'montantTotal': rec_stats['montantTotal'] or 0,
            'commissionTotale': rec_stats['commissionTotale'] or 0,
            'totalPDV': total_pdv,
        }

        return Response(data)

    def create(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserReadSerializer(user).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
        except (User.DoesNotExist, ValueError):
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': 'Utilisateur introuvable'}},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UserUpdateSerializer(
            data=request.data, context={'user': user},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.update(user, serializer.validated_data)
        return Response(UserReadSerializer(user).data)

    def destroy(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
        except (User.DoesNotExist, ValueError):
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': 'Utilisateur introuvable'}},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.role == 'admin':
            admin_count = User.objects.filter(role='admin', is_active=True).count()
            if admin_count <= 1:
                return Response(
                    {'error': {'code': 'CONFLICT', 'message': 'Impossible de desactiver le dernier administrateur'}},
                    status=status.HTTP_409_CONFLICT,
                )

        user.is_active = False
        user.save()
        return Response({'message': 'Utilisateur desactive'})
