from django.urls import path
from . import views

app_name = 'licensing'

urlpatterns = [
    path('activate/', views.activate_license, name='activate'),
    path('validate/', views.validate_license, name='validate'),
    path('deactivate/', views.deactivate_license, name='deactivate'),
]
