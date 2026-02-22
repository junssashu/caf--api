from django.urls import path

from pdv.views import PDVViewSet

pdv_list = PDVViewSet.as_view({'get': 'list', 'post': 'create'})
pdv_detail = PDVViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
    'delete': 'destroy',
})

urlpatterns = [
    path('pdv/', pdv_list, name='pdv-list'),
    path('pdv/<str:pk>/', pdv_detail, name='pdv-detail'),
]
