from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_contratos, name='lista_contratos'),
    path('contrato/<int:contrato_id>/', views.detalhe_contrato, name='detalhe_contrato'),
]
