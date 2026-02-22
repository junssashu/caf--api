from django.urls import path

from accounts.views import LoginView, LogoutView, UserViewSet

user_list = UserViewSet.as_view({'get': 'list', 'post': 'create'})
user_detail = UserViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
    'delete': 'destroy',
})

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('users/', user_list, name='user-list'),
    path('users/<str:pk>/', user_detail, name='user-detail'),
]
