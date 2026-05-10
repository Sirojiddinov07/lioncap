from django.contrib import admin
from django.utils.html import format_html
from .models import MaterialIssue, ProductReceipt, MasterBalance


class ProductReceiptInline(admin.TabularInline):
    model = ProductReceipt
    extra = 0
    fields = ['product', 'quantity_received', 'quality_status', 'defect_reason', 'actual_weight_per_item', 'receipt_date']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MaterialIssue)
class MaterialIssueAdmin(admin.ModelAdmin):
    list_display = ['id', 'master', 'issue_date', 'created_at', 'thread', 'quantity', 'expected_quantity', 'is_closed']
    list_filter = ['is_closed', 'issue_date', 'created_at', 'master']
    search_fields = ['master__username', 'master__first_name', 'master__last_name', 'thread__name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProductReceiptInline]

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('master', 'thread', 'quantity', 'note')
        }),
        ('Kutilayotgan mahsulot', {
            'fields': ('expected_product', 'expected_quantity')
        }),
        ('Vaqt ma\'lumotlari', {
            'fields': ('issue_date',),  # issue_date faqat o'qish uchun
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductReceipt)
class ProductReceiptAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'material_issue', 'receipt_date', 'created_at',
        'product', 'quantity_received', 'quality_status', 'total_weight_display'
    ]
    list_filter = ['quality_status', 'defect_reason', 'receipt_date', 'created_at']
    search_fields = ['material_issue__master__username']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('material_issue', 'product', 'quantity_received', 'quality_status', 'defect_reason', 'note')
        }),
        ('Og\'irlik va to\'lov', {
            'fields': ('actual_weight_per_item',)
        }),
        ('Vaqt ma\'lumotlari', {
            'fields': ('receipt_date',),
            'classes': ('collapse',)
        }),
    )

    def total_weight_display(self, obj):
        return f"{obj.total_weight} kg"
    total_weight_display.short_description = "Og'irlik"


@admin.register(MasterBalance)
class MasterBalanceAdmin(admin.ModelAdmin):
    list_display = [
        'master', 'total_product_given', 'total_payment_due_uzs', 'total_payment_paid_uzs',
        'total_payment_due_usd', 'total_payment_paid_usd', 'product_debt_display', 'created_at'
    ]
    search_fields = ['master__username', 'master__first_name', 'master__last_name']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Usta va mahsulotlar', {
            'fields': ('master', 'total_product_given', 'total_weight_given')
        }),
        ('To\'lovlar (so\'m)', {
            'fields': ('total_payment_due_uzs', 'total_payment_paid_uzs')
        }),
        ('To\'lovlar (dollar)', {
            'fields': ('total_payment_due_usd', 'total_payment_paid_usd')
        }),
        ('Vaqt ma\'lumotlari', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def product_debt_display(self, obj):
        return f"{obj.product_debt} dona"
    product_debt_display.short_description = "Mahsulot qarzi"