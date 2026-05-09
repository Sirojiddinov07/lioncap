from django.contrib import admin
from .models import Thread, ThreadTransaction, ThreadSupplierDebt, SupplierPayment


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'current_stock', 'price_per_unit', 'is_low_stock']
    list_filter = ['color']
    search_fields = ['name', 'article']

    def is_low_stock(self, obj):
        return obj.is_low_stock

    is_low_stock.boolean = True
    is_low_stock.short_description = "Zaxira kam"


@admin.register(ThreadTransaction)
class ThreadTransactionAdmin(admin.ModelAdmin):
    list_display = ['thread', 'quantity', 'transaction_type', 'related_master', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['thread__name', 'related_master__username', 'note']
    readonly_fields = ['created_at']


@admin.register(ThreadSupplierDebt)
class ThreadSupplierDebtAdmin(admin.ModelAdmin):
    list_display = ['thread', 'quantity', 'amount', 'paid_amount', 'remaining_amount', 'is_paid', 'created_at']
    list_filter = ['is_paid', 'thread']
    search_fields = ['thread__name', 'note']
    readonly_fields = ['remaining_amount', 'created_at', 'updated_at']

    def remaining_amount(self, obj):
        return f"{obj.remaining_amount:,.0f} so'm"

    remaining_amount.short_description = "Qolgan qarz"

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('thread', 'quantity', 'amount', 'payment_type', 'note')
        }),
        ('To\'lov ma\'lumotlari', {
            'fields': ('paid_amount', 'is_paid'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SupplierPayment)
class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = ['debt', 'amount', 'created_at', 'created_by']
    list_filter = ['created_at']
    search_fields = ['debt__thread__name', 'note']
    readonly_fields = ['created_at']