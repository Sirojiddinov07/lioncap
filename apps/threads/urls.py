from django.urls import path
from . import views

app_name = 'threads'

urlpatterns = [
    path('', views.ThreadListView.as_view(), name='list'),
    path('incoming/', views.thread_incoming, name='incoming'),
    path('transactions/', views.transaction_list, name='transactions'),
    path('supplier-debts/', views.supplier_debts, name='supplier_debts'),
    path('supplier-debts/pay/<int:debt_id>/', views.pay_supplier_debt, name='pay_supplier_debt'),
    path('add-credit/', views.add_credit_only, name='add_credit_only'),
    path('add-credit-page/', views.add_credit_only, name='add_credit_page'),  # Qo'shimcha nom
]