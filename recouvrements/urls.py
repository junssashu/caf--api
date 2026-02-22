from django.urls import path

from recouvrements.views import RecouvrementViewSet

rec_list = RecouvrementViewSet.as_view({'get': 'list', 'post': 'create'})
rec_detail = RecouvrementViewSet.as_view({'get': 'retrieve'})
rec_status = RecouvrementViewSet.as_view({'patch': 'update_status'})

urlpatterns = [
    path('recouvrements/', rec_list, name='recouvrement-list'),
    path('recouvrements/<str:pk>/', rec_detail, name='recouvrement-detail'),
    path('recouvrements/<str:pk>/status/', rec_status, name='recouvrement-status'),
]
