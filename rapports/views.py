from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from core.permissions import IsAdmin, IsAgent
from pdv.models import PointDeVente
from recouvrements.models import LigneRecouvrement, Recouvrement
from recouvrements.serializers import RecouvrementListSerializer

# --- Date filter params (shared) ---
_DATE_PARAMS = [
    OpenApiParameter('startDate', str, description='Date debut (YYYY-MM-DD)'),
    OpenApiParameter('endDate', str, description='Date fin (YYYY-MM-DD)'),
]


# --- Schema serializers ---
class _SummarySerializer(drf_serializers.Serializer):
    totalRecouvrements = drf_serializers.IntegerField()
    montantTotal = drf_serializers.IntegerField()
    commissionTotale = drf_serializers.IntegerField()
    tauxValidation = drf_serializers.FloatField()
    pdvActifs = drf_serializers.IntegerField()
    agentsActifs = drf_serializers.IntegerField()


class _ParJourItemSerializer(drf_serializers.Serializer):
    date = drf_serializers.DateField()
    montant = drf_serializers.IntegerField()
    count = drf_serializers.IntegerField()


class _ParJourResponseSerializer(drf_serializers.Serializer):
    data = _ParJourItemSerializer(many=True)


class _ParCategorieItemSerializer(drf_serializers.Serializer):
    categorie = drf_serializers.CharField()
    label = drf_serializers.CharField()
    quantiteTotale = drf_serializers.IntegerField()
    montantTotal = drf_serializers.IntegerField()


class _ParCategorieResponseSerializer(drf_serializers.Serializer):
    data = _ParCategorieItemSerializer(many=True)


class _ParMethodeItemSerializer(drf_serializers.Serializer):
    methode = drf_serializers.CharField()
    label = drf_serializers.CharField()
    count = drf_serializers.IntegerField()
    total = drf_serializers.IntegerField()


class _ParMethodeResponseSerializer(drf_serializers.Serializer):
    data = _ParMethodeItemSerializer(many=True)


class _TopAgentItemSerializer(drf_serializers.Serializer):
    agentId = drf_serializers.UUIDField()
    nom = drf_serializers.CharField()
    totalRecouvrements = drf_serializers.IntegerField()
    montantTotal = drf_serializers.IntegerField()
    commissionTotale = drf_serializers.IntegerField()


class _TopAgentsResponseSerializer(drf_serializers.Serializer):
    data = _TopAgentItemSerializer(many=True)


class _TopPDVItemSerializer(drf_serializers.Serializer):
    pdvId = drf_serializers.UUIDField()
    nom = drf_serializers.CharField()
    totalRecouvrements = drf_serializers.IntegerField()
    montantTotal = drf_serializers.IntegerField()


class _TopPDVsResponseSerializer(drf_serializers.Serializer):
    data = _TopPDVItemSerializer(many=True)


def _date_filter(request, qs, field='created_at'):
    start = request.query_params.get('startDate')
    end = request.query_params.get('endDate')
    if start:
        qs = qs.filter(**{f'{field}__date__gte': start})
    if end:
        qs = qs.filter(**{f'{field}__date__lte': end})
    return qs


class SummaryView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(tags=['Rapports'], summary='Resume global', parameters=_DATE_PARAMS, responses={200: _SummarySerializer})
    def get(self, request):
        qs = _date_filter(request, Recouvrement.objects.all())

        stats = qs.aggregate(
            totalRecouvrements=Count('id'),
            montantTotal=Sum('montant'),
            commissionTotale=Sum('commission'),
            recouvrementsEnAttente=Count('id', filter=Q(status='EN_ATTENTE')),
            recouvrementsValides=Count('id', filter=Q(status='VALIDE')),
            recouvrementsRejetes=Count('id', filter=Q(status='REJETE')),
        )

        for k in ('montantTotal', 'commissionTotale'):
            if stats[k] is None:
                stats[k] = 0

        valides = stats['recouvrementsValides']
        rejetes = stats['recouvrementsRejetes']
        total_resolus = valides + rejetes
        stats['tauxValidation'] = round(valides / total_resolus * 100, 2) if total_resolus > 0 else 0

        stats['pdvActifs'] = PointDeVente.objects.filter(status='ACTIF').count()
        stats['agentsActifs'] = User.objects.filter(role='agent', is_active=True).count()

        return Response(stats)


class ParJourView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(tags=['Rapports'], summary='Revenus par jour', parameters=_DATE_PARAMS, responses={200: _ParJourResponseSerializer})
    def get(self, request):
        qs = _date_filter(request, Recouvrement.objects.all())

        data = (
            qs.annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(montant=Sum('montant'), count=Count('id'))
            .order_by('date')
        )

        return Response({
            'data': [
                {'date': str(row['date']), 'montant': row['montant'], 'count': row['count']}
                for row in data
            ]
        })


class ParCategorieView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(tags=['Rapports'], summary='Ventes par categorie', parameters=_DATE_PARAMS, responses={200: _ParCategorieResponseSerializer})
    def get(self, request):
        qs = LigneRecouvrement.objects.all()

        start = request.query_params.get('startDate')
        end = request.query_params.get('endDate')
        if start:
            qs = qs.filter(recouvrement__created_at__date__gte=start)
        if end:
            qs = qs.filter(recouvrement__created_at__date__lte=end)

        from core.enums import CategorieProduit
        label_map = dict(CategorieProduit.choices)

        data = (
            qs.values('categorie')
            .annotate(
                quantiteTotale=Sum('quantite'),
                montantTotal=Sum('sous_total'),
            )
            .order_by('-montantTotal')
        )

        return Response({
            'data': [
                {
                    'categorie': row['categorie'],
                    'label': label_map.get(row['categorie'], row['categorie']),
                    'quantiteTotale': row['quantiteTotale'],
                    'montantTotal': row['montantTotal'],
                }
                for row in data
            ]
        })


class ParMethodeView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(tags=['Rapports'], summary='Repartition par methode de paiement', parameters=_DATE_PARAMS, responses={200: _ParMethodeResponseSerializer})
    def get(self, request):
        qs = _date_filter(request, Recouvrement.objects.all())

        from core.enums import MethodePaiement
        label_map = dict(MethodePaiement.choices)

        data = (
            qs.values('methode_paiement')
            .annotate(count=Count('id'), total=Sum('montant'))
            .order_by('-total')
        )

        return Response({
            'data': [
                {
                    'methode': row['methode_paiement'],
                    'label': label_map.get(row['methode_paiement'], row['methode_paiement']),
                    'count': row['count'],
                    'total': row['total'],
                }
                for row in data
            ]
        })


class TopAgentsView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        tags=['Rapports'], summary='Top agents par montant',
        parameters=_DATE_PARAMS + [OpenApiParameter('limit', int, description='Nombre max de resultats (defaut 10)')],
        responses={200: _TopAgentsResponseSerializer},
    )
    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        qs = _date_filter(request, Recouvrement.objects.all())

        data = (
            qs.values('agent_id', 'agent__nom')
            .annotate(
                totalRecouvrements=Count('id'),
                montantTotal=Sum('montant'),
                commissionTotale=Sum('commission'),
            )
            .order_by('-montantTotal')[:limit]
        )

        return Response({
            'data': [
                {
                    'agentId': str(row['agent_id']),
                    'nom': row['agent__nom'],
                    'totalRecouvrements': row['totalRecouvrements'],
                    'montantTotal': row['montantTotal'],
                    'commissionTotale': row['commissionTotale'],
                }
                for row in data
            ]
        })


class TopPDVsView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        tags=['Rapports'], summary='Top points de vente par montant',
        parameters=_DATE_PARAMS + [OpenApiParameter('limit', int, description='Nombre max de resultats (defaut 10)')],
        responses={200: _TopPDVsResponseSerializer},
    )
    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        qs = _date_filter(request, Recouvrement.objects.all())

        data = (
            qs.values('point_de_vente_id', 'point_de_vente__nom')
            .annotate(
                totalRecouvrements=Count('id'),
                montantTotal=Sum('montant'),
            )
            .order_by('-montantTotal')[:limit]
        )

        return Response({
            'data': [
                {
                    'pdvId': str(row['point_de_vente_id']),
                    'nom': row['point_de_vente__nom'],
                    'totalRecouvrements': row['totalRecouvrements'],
                    'montantTotal': row['montantTotal'],
                }
                for row in data
            ]
        })


class AdminStatsView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(tags=['Stats'], summary='Statistiques dashboard admin')
    def get(self, request):
        all_recs = Recouvrement.objects.all()

        stats = all_recs.aggregate(
            totalRecouvrements=Count('id'),
            montantTotal=Sum('montant'),
            commissionTotale=Sum('commission'),
        )
        for k in ('montantTotal', 'commissionTotale'):
            if stats[k] is None:
                stats[k] = 0

        stats['pdvActifs'] = PointDeVente.objects.filter(status='ACTIF').count()
        stats['agentsActifs'] = User.objects.filter(role='agent', is_active=True).count()

        valides = all_recs.filter(status='VALIDE').count()
        rejetes = all_recs.filter(status='REJETE').count()
        total_resolus = valides + rejetes
        stats['tauxValidation'] = round(valides / total_resolus * 100, 2) if total_resolus > 0 else 0

        # Revenue par jour (last 14 days)
        fourteen_days_ago = timezone.now().date() - timedelta(days=14)
        daily = (
            all_recs.filter(created_at__date__gte=fourteen_days_ago)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(montant=Sum('montant'))
            .order_by('date')
        )
        stats['revenueParJour'] = [
            {'date': str(row['date']), 'montant': row['montant']}
            for row in daily
        ]

        # Recent recouvrements (last 5)
        recent = (
            all_recs.select_related('point_de_vente', 'agent')
            .prefetch_related('lignes')
            .order_by('-created_at')[:5]
        )
        stats['recentRecouvrements'] = [
            {
                'id': str(r.id),
                'code': r.code,
                'pointDeVenteNom': r.point_de_vente.nom,
                'agentNom': r.agent.nom,
                'montant': r.montant,
                'methodePaiement': r.methode_paiement,
                'status': r.status,
                'createdAt': r.created_at.isoformat(),
            }
            for r in recent
        ]

        # Par methode
        par_methode_qs = (
            all_recs.values('methode_paiement')
            .annotate(count=Count('id'), total=Sum('montant'))
        )
        stats['parMethode'] = {
            row['methode_paiement']: {'count': row['count'], 'total': row['total']}
            for row in par_methode_qs
        }

        # Top agents (top 5)
        top_agents = (
            all_recs.values('agent__nom')
            .annotate(total=Sum('montant'))
            .order_by('-total')[:5]
        )
        stats['topAgents'] = [
            {'nom': row['agent__nom'], 'total': row['total']}
            for row in top_agents
        ]

        return Response(stats)


class AgentStatsView(APIView):
    permission_classes = [IsAgent]

    @extend_schema(tags=['Stats'], summary='Statistiques dashboard agent')
    def get(self, request):
        agent_recs = Recouvrement.objects.filter(agent_id=request.user.id)

        stats = agent_recs.aggregate(
            totalRecouvrements=Count('id'),
            montantTotal=Sum('montant'),
            recouvrementsEnAttente=Count('id', filter=Q(status='EN_ATTENTE')),
        )
        for k in ('montantTotal',):
            if stats[k] is None:
                stats[k] = 0

        stats['totalPDV'] = PointDeVente.objects.filter(agent_id=request.user.id).count()

        recent = (
            agent_recs.select_related('point_de_vente', 'agent')
            .prefetch_related('lignes')
            .order_by('-created_at')[:5]
        )
        stats['recentRecouvrements'] = [
            {
                'id': str(r.id),
                'code': r.code,
                'pointDeVenteNom': r.point_de_vente.nom,
                'articlesSummary': r.articles_summary,
                'montant': r.montant,
                'methodePaiement': r.methode_paiement,
                'status': r.status,
                'createdAt': r.created_at.isoformat(),
            }
            for r in recent
        ]

        return Response(stats)
