from django.contrib import admin
from django.utils.html import format_html
from .models import MaterialIssue, ProductReceipt, MasterBalance


class ProductReceiptInline(admin.TabularInline):
    model = ProductReceipt
    extra = 0
    fields = ['product', 'quantity_received', 'quality_status', 'defect_reason', 'actual_weight_per_item']
    readonly_fields = ['total_weight_display']

    def total_weight_display(self, obj):
        return f"{obj.total_weight} kg"

    total_weight_display.short_description = "Umumiy og'irlik"


@admin.register(MaterialIssue)
class MaterialIssueAdmin(admin.ModelAdmin):
    list_display = ['id', 'master', 'issue_date', 'thread', 'quantity', 'expected_quantity', 'is_closed']
    list_filter = ['is_closed', 'issue_date', 'master']
    search_fields = ['master__username', 'master__first_name', 'master__last_name', 'thread__name']
    readonly_fields = ['current_balance_quantity_display']
    inlines = [ProductReceiptInline]

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('master', 'thread', 'quantity', 'note')
        }),
        ('Kutilayotgan mahsulot', {
            'fields': ('expected_product', 'expected_quantity')
        }),
    )

    def current_balance_quantity_display(self, obj):
        return f"{obj.current_balance_quantity} dona"

    current_balance_quantity_display.short_description = "Joriy qarz"


@admin.register(ProductReceipt)
class ProductReceiptAdmin(admin.ModelAdmin):
    list_display = ['id', 'material_issue', 'receipt_date', 'product', 'quantity_received', 'quality_status',
                    'total_weight_display']
    list_filter = ['quality_status', 'defect_reason', 'receipt_date']
    search_fields = ['material_issue__master__username']
    readonly_fields = ['total_weight_display', 'total_payment_display']

    def total_weight_display(self, obj):
        return f"{obj.total_weight} kg"

    total_weight_display.short_description = "Og'irlik"

    def total_payment_display(self, obj):
        if obj.quality_status == 'good':
            currency = obj.material_issue.master.preferred_currency
            return f"{obj.total_payment:,.2f} {currency.upper()}"
        return "-"

    total_payment_display.short_description = "To'lov"


@admin.register(MasterBalance)
class MasterBalanceAdmin(admin.ModelAdmin):
    list_display = [
        'master', 'total_product_given', 'total_payment_due_uzs', 'total_payment_paid_uzs',
        'total_payment_due_usd', 'total_payment_paid_usd', 'product_debt_display'
    ]
    search_fields = ['master__username', 'master__first_name', 'master__last_name']
    readonly_fields = [
        'total_product_given', 'total_weight_given',
        'total_payment_due_uzs', 'total_payment_paid_uzs',
        'total_payment_due_usd', 'total_payment_paid_usd',
        'product_debt_display', 'payment_balance_uzs_display', 'payment_balance_usd_display'
    ]

    def product_debt_display(self, obj):
        return f"{obj.product_debt} dona"

    product_debt_display.short_description = "Mahsulot qarzi"

    def payment_balance_uzs_display(self, obj):
        return f"{obj.payment_balance_uzs:,.0f} so'm"

    payment_balance_uzs_display.short_description = "Qolgan qarz (so'm)"

    def payment_balance_usd_display(self, obj):
        return f"{obj.payment_balance_usd:,.2f} USD"

    payment_balance_usd_display.short_description = "Qolgan qarz (dollar)"