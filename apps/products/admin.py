from django.contrib import admin
from .models import Product, ProductThread


class ProductThreadInline(admin.TabularInline):
    model = ProductThread
    extra = 1
    fields = ['thread', 'quantity_per_unit']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'standard_weight', 'weaving_price_uzs', 'weaving_price_usd', 'is_active']
    list_filter = ['is_active', 'default_thread']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProductThreadInline]

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'code', 'is_active')
        }),
        ('Og\'irlik', {
            'fields': ('standard_weight',)
        }),
        ('Narxlar', {
            'fields': ('weaving_price_uzs', 'weaving_price_usd'),
        }),
        ('Ip', {
            'fields': ('default_thread',)
        }),
    )


@admin.register(ProductThread)
class ProductThreadAdmin(admin.ModelAdmin):
    list_display = ['product', 'thread', 'quantity_per_unit']
    list_filter = ['product', 'thread']
    search_fields = ['product__name', 'thread__name']