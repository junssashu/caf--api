from django.urls import path

from rapports.views import (
    AdminStatsView,
    AgentStatsView,
    ParCategorieView,
    ParJourView,
    ParMethodeView,
    SummaryView,
    TopAgentsView,
    TopPDVsView,
)

urlpatterns = [
    path('rapports/summary/', SummaryView.as_view(), name='rapports-summary'),
    path('rapports/par-jour/', ParJourView.as_view(), name='rapports-par-jour'),
    path('rapports/par-categorie/', ParCategorieView.as_view(), name='rapports-par-categorie'),
    path('rapports/par-methode/', ParMethodeView.as_view(), name='rapports-par-methode'),
    path('rapports/top-agents/', TopAgentsView.as_view(), name='rapports-top-agents'),
    path('rapports/top-pdvs/', TopPDVsView.as_view(), name='rapports-top-pdvs'),
    path('admin/stats/', AdminStatsView.as_view(), name='admin-stats'),
    path('agent/stats/', AgentStatsView.as_view(), name='agent-stats'),
]
