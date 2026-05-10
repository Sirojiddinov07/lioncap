from django.contrib import admin
from django.utils.html import format_html
from .models import Product, ProductThread


class ProductThreadInline(admin.TabularInline):
    model = ProductThread
    extra = 1
    fields = ['thread', 'quantity_per_unit', 'created_at', 'updated_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'standard_weight', 'stock_quantity', 'stock_status', 'weaving_price_uzs',
                    'weaving_price_usd', 'is_active', 'created_at']
    list_filter = ['is_active', 'default_thread', 'created_at']
    search_fields = ['name', 'code']
    inlines = [ProductThreadInline]

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'code', 'image', 'is_active')
        }),
        ('Og\'irlik va son', {
            'fields': ('standard_weight', 'stock_quantity', 'min_stock_threshold'),
        }),
        ('Narxlar', {
            'fields': ('weaving_price_uzs', 'weaving_price_usd'),
        }),
        ('Ip', {
            'fields': ('default_thread',)
        }),
        ('Vaqt ma\'lumotlari (tahrirlash mumkin)', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('wide',)
        }),
    )

    def stock_status(self, obj):
        if obj.is_out_of_stock:
            return format_html('<span style="color: red;">✗ Tugagan</span>')
        elif obj.is_low_stock:
            return format_html('<span style="color: orange;">⚠ Kam</span>')
        return format_html('<span style="color: green;">✓ Yetarli</span>')

    stock_status.short_description = "Zaxira holati"


@admin.register(ProductThread)
class ProductThreadAdmin(admin.ModelAdmin):
    list_display = ['product', 'thread', 'quantity_per_unit', 'created_at']
    list_filter = ['product', 'thread', 'created_at']
    search_fields = ['product__name', 'thread__name']

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('product', 'thread', 'quantity_per_unit')
        }),
        ('Vaqt ma\'lumotlari (tahrirlash mumkin)', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('wide',)
        }),
    )