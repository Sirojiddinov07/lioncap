from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='list'),
    path('create/', views.product_create, name='create'),
    path('<int:pk>/edit/', views.product_edit, name='edit'),
    path('<int:pk>/detail/', views.product_detail, name='detail'),  # YANGI

]