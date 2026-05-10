from django import forms
from .models import Product
from apps.threads.models import Thread

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'code', 'image', 'standard_weight', 'stock_quantity',
            'min_stock_threshold', 'weaving_price_uzs', 'weaving_price_usd',
            'default_thread', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'standard_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'min_stock_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'weaving_price_uzs': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00001'}),
            'weaving_price_usd': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00001'}),
            'default_thread': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }