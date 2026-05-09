from django import forms
from .models import Product
from apps.threads.models import Thread

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'code', 'standard_weight',
            'weaving_price_uzs', 'weaving_price_usd',
            'default_thread', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'standard_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'weaving_price_uzs': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'weaving_price_usd': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'default_thread': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }