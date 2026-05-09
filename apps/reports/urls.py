from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.main_report, name='main'),
    path('masters/', views.masters_report, name='masters'),
    path('products/', views.products_report, name='products'),
    path('financial/', views.financial_report, name='financial'),
]