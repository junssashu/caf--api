from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from core.pagination import CAFPagination
from core.permissions import IsAdmin, IsAdminOrAgent
from core.utils import generate_code
from pdv.models import PointDeVente
from pdv.serializers import PDVCreateSerializer, PDVListSerializer, PDVUpdateSerializer


@extend_schema_view(
    list=extend_schema(
        tags=['PDV'], summary='Lister les points de vente',
        parameters=[
            OpenApiParameter('search', str, description='Recherche par nom, code, proprietaire'),
            OpenApiParameter('status', str, description='Filtrer par statut (ACTIF/EN_ATTENTE/INACTIF)'),
            OpenApiParameter('agentId', str, description='Filtrer par agent'),
        ],
    ),
    retrieve=extend_schema(tags=['PDV'], summary='Detail point de vente'),
    create=extend_schema(tags=['PDV'], summary='Creer un point de vente', request=PDVCreateSerializer, responses={201: PDVListSerializer}),
    partial_update=extend_schema(tags=['PDV'], summary='Modifier un point de vente', request=PDVUpdateSerializer, responses={200: PDVListSerializer}),
    destroy=extend_schema(tags=['PDV'], summary='Supprimer un point de vente'),
)
class PDVViewSet(ViewSet):
    def get_permissions(self):
        if self.action in ('partial_update', 'destroy'):
            return [IsAdmin()]
        return [IsAdminOrAgent()]

    def get_queryset(self, request):
        qs = PointDeVente.objects.select_related('agent').order_by('-created_at')
        if request.user.role == 'agent':
            qs = qs.filter(agent_id=request.user.id)
        return qs

    def list(self, request):
        qs = self.get_queryset(request)

        pdv_status = request.query_params.get('status')
        if pdv_status:
            qs = qs.filter(status=pdv_status)

        agent_id = request.query_params.get('agentId')
        if agent_id and request.user.role == 'admin':
            qs = qs.filter(agent_id=agent_id)

        commune = request.query_params.get('commune')
        if commune:
            qs = qs.filter(commune=commune)

        search = request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(nom__icontains=search)
                | Q(code__icontains=search)
                | Q(proprietaire_nom__icontains=search)
            )

        paginator = CAFPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = PDVListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            pdv = self.get_queryset(request).get(pk=pk)
        except (PointDeVente.DoesNotExist, ValueError):
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': 'Point de vente introuvable'}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(PDVListSerializer(pdv).data)

    def create(self, request):
        serializer = PDVCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        code = generate_code('CAF', PointDeVente)

        if request.user.role == 'agent':
            agent_id = request.user.id
            pdv_status = 'EN_ATTENTE'
        else:
            agent_id = data.get('agentId')
            if not agent_id:
                return Response(
                    {'error': {'code': 'VALIDATION_ERROR', 'message': "L'agentId est requis"}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            pdv_status = data.get('status', 'EN_ATTENTE')

        pdv = PointDeVente.objects.create(
            code=code,
            nom=data['nom'],
            adresse=data.get('adresse') or None,
            ville=data.get('ville', 'Abidjan'),
            commune=data['commune'],
            proprietaire_nom=data['proprietaireNom'],
            proprietaire_telephone=data.get('proprietaireTelephone') or None,
            status=pdv_status,
            agent_id=agent_id,
        )
        pdv = PointDeVente.objects.select_related('agent').get(pk=pdv.pk)
        return Response(PDVListSerializer(pdv).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        try:
            pdv = PointDeVente.objects.select_related('agent').get(pk=pk)
        except (PointDeVente.DoesNotExist, ValueError):
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': 'Point de vente introuvable'}},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PDVUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        for field_map in [
            ('nom', 'nom'),
            ('adresse', 'adresse'),
            ('ville', 'ville'),
            ('commune', 'commune'),
            ('proprietaireNom', 'proprietaire_nom'),
            ('proprietaireTelephone', 'proprietaire_telephone'),
            ('status', 'status'),
        ]:
            camel, snake = field_map
            if camel in data:
                setattr(pdv, snake, data[camel])

        if 'agentId' in data:
            pdv.agent_id = data['agentId']

        pdv.save()
        pdv.refresh_from_db()
        pdv = PointDeVente.objects.select_related('agent').get(pk=pdv.pk)
        return Response(PDVListSerializer(pdv).data)

    def destroy(self, request, pk=None):
        try:
            pdv = PointDeVente.objects.get(pk=pk)
        except (PointDeVente.DoesNotExist, ValueError):
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': 'Point de vente introuvable'}},
                status=status.HTTP_404_NOT_FOUND,
            )

        from recouvrements.models import Recouvrement
        if Recouvrement.objects.filter(point_de_vente_id=pdv.id).exists():
            return Response(
                {'error': {'code': 'CONFLICT', 'message': 'Ce point de vente a des recouvrements associes et ne peut pas etre supprime'}},
                status=status.HTTP_409_CONFLICT,
            )

        pdv.delete()
        return Response({'message': 'Point de vente supprime'})
