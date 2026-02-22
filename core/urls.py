from django.urls import path

from core.views import CommissionUpdateView, ProfileUpdateView, SettingsView

urlpatterns = [
    path('settings/', SettingsView.as_view(), name='settings'),
    path('settings/profile/', ProfileUpdateView.as_view(), name='settings-profile'),
    path('settings/commission/', CommissionUpdateView.as_view(), name='settings-commission'),
]
