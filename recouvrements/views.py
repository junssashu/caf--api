from decimal import Decimal

from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from core.exceptions import StatusConflictError
from core.models import Settings
from core.pagination import CAFPagination
from core.permissions import IsAdmin, IsAdminOrAgent, IsAgent
from core.utils import generate_code
from pdv.models import PointDeVente
from recouvrements.models import LigneRecouvrement, Recouvrement
from recouvrements.serializers import (
    RecouvrementCreateSerializer,
    RecouvrementListSerializer,
    StatusUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(
        tags=['Recouvrements'], summary='Lister les recouvrements',
        parameters=[
            OpenApiParameter('search', str, description='Recherche par code, PDV'),
            OpenApiParameter('status', str, description='Filtrer par statut (EN_ATTENTE/VALIDE/REJETE)'),
            OpenApiParameter('methodePaiement', str, description='Filtrer par methode (MTN_MOMO/ORANGE_MONEY/ESPECES)'),
            OpenApiParameter('agentId', str, description='Filtrer par agent'),
            OpenApiParameter('pointDeVenteId', str, description='Filtrer par PDV'),
            OpenApiParameter('startDate', str, description='Date debut (YYYY-MM-DD)'),
            OpenApiParameter('endDate', str, description='Date fin (YYYY-MM-DD)'),
        ],
    ),
    retrieve=extend_schema(tags=['Recouvrements'], summary='Detail recouvrement'),
    create=extend_schema(tags=['Recouvrements'], summary='Creer un recouvrement', request=RecouvrementCreateSerializer, responses={201: RecouvrementListSerializer}),
    update_status=extend_schema(tags=['Recouvrements'], summary='Valider/Rejeter un recouvrement', request=StatusUpdateSerializer, responses={200: RecouvrementListSerializer}),
)
class RecouvrementViewSet(ViewSet):
    def get_permissions(self):
        if self.action == 'create':
            return [IsAgent()]
        if self.action == 'update_status':
            return [IsAdmin()]
        return [IsAdminOrAgent()]

    def get_queryset(self, request):
        qs = Recouvrement.objects.select_related('point_de_vente', 'agent').prefetch_related('lignes')
        if request.user.role == 'agent':
            qs = qs.filter(agent_id=request.user.id)
        return qs

    def list(self, request):
        qs = self.get_queryset(request)

        rec_status = request.query_params.get('status')
        if rec_status:
            qs = qs.filter(status=rec_status)

        methode = request.query_params.get('methode')
        if methode:
            qs = qs.filter(methode_paiement=methode)

        categorie = request.query_params.get('categorie')
        if categorie:
            qs = qs.filter(lignes__categorie=categorie).distinct()

        pdv_id = request.query_params.get('pdvId')
        if pdv_id:
            qs = qs.filter(point_de_vente_id=pdv_id)

        agent_id = request.query_params.get('agentId')
        if agent_id and request.user.role == 'admin':
            qs = qs.filter(agent_id=agent_id)

        start_date = request.query_params.get('startDate')
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)

        end_date = request.query_params.get('endDate')
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        search = request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(code__icontains=search)
                | Q(point_de_vente__nom__icontains=search)
                | Q(agent__nom__icontains=search)
            )

        sort_field = request.query_params.get('sort', 'createdAt')
        sort_order = request.query_params.get('order', 'desc')

        sort_map = {
            'createdAt': 'created_at',
            'montant': 'montant',
            'status': 'status',
            'code': 'code',
        }
        db_field = sort_map.get(sort_field, 'created_at')
        if sort_order == 'desc':
            db_field = f'-{db_field}'
        qs = qs.order_by(db_field)

        paginator = CAFPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = RecouvrementListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            rec = self.get_queryset(request).get(pk=pk)
        except (Recouvrement.DoesNotExist, ValueError):
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': 'Recouvrement introuvable'}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(RecouvrementListSerializer(rec).data)

    def create(self, request):
        serializer = RecouvrementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Validate PDV
        try:
            pdv = PointDeVente.objects.get(pk=data['pointDeVenteId'])
        except PointDeVente.DoesNotExist:
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': 'Point de vente introuvable'}},
                status=status.HTTP_404_NOT_FOUND,
            )

        if pdv.agent_id != request.user.id:
            return Response(
                {'error': {'code': 'FORBIDDEN', 'message': 'Le point de vente ne vous est pas attribue'}},
                status=status.HTTP_403_FORBIDDEN,
            )

        if pdv.status != 'ACTIF':
            return Response(
                {'error': {'code': 'UNPROCESSABLE_ENTITY', 'message': "Le point de vente n'est pas actif"}},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # Compute
        settings = Settings.get()
        taux_decimal = settings.taux_commission / Decimal('100')

        lignes_data = data['lignes']
        computed_lignes = []
        montant_total = 0
        for l in lignes_data:
            sous_total = l['prixUnitaire'] * l['quantite']
            montant_total += sous_total
            computed_lignes.append({
                'nom_produit': l['nomProduit'],
                'categorie': l['categorie'],
                'prix_unitaire': l['prixUnitaire'],
                'quantite': l['quantite'],
                'sous_total': sous_total,
            })

        commission = round(montant_total * float(taux_decimal))
        code = generate_code('REC', Recouvrement)

        rec = Recouvrement.objects.create(
            code=code,
            point_de_vente=pdv,
            agent=request.user,
            montant=montant_total,
            taux_commission=taux_decimal,
            commission=commission,
            methode_paiement=data['methodePaiement'],
            status='EN_ATTENTE',
            reference=data.get('reference') or None,
            notes=data.get('notes') or None,
        )

        for cl in computed_lignes:
            LigneRecouvrement.objects.create(recouvrement=rec, **cl)

        rec = Recouvrement.objects.select_related(
            'point_de_vente', 'agent',
        ).prefetch_related('lignes').get(pk=rec.pk)

        return Response(
            RecouvrementListSerializer(rec).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        try:
            rec = Recouvrement.objects.select_related(
                'point_de_vente', 'agent',
            ).prefetch_related('lignes').get(pk=pk)
        except (Recouvrement.DoesNotExist, ValueError):
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': 'Recouvrement introuvable'}},
                status=status.HTTP_404_NOT_FOUND,
            )

        if rec.status != 'EN_ATTENTE':
            raise StatusConflictError()

        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        rec.status = new_status

        if new_status == 'VALIDE':
            rec.validated_at = timezone.now()

        rec.save()

        return Response(RecouvrementListSerializer(rec).data)
