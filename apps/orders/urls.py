from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('masters/', views.master_list, name='master_list'),
    path('masters/<int:master_id>/', views.master_detail, name='master_detail'),
    path('issue/create/', views.issue_create, name='issue_create'),
    path('receipt/create/<int:issue_id>/', views.receipt_create, name='receipt_create'),
    path('payment/add/<int:master_id>/', views.add_payment, name='add_payment'),
    path('finished-products/', views.finished_products, name='finished_products'),
]