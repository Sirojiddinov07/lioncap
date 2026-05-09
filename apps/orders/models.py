from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Sum
from apps.core.models import BaseModel
from apps.core.constants import QualityStatus, DefectReason, CurrencyType, TransactionType
from apps.users.models import User
from apps.threads.models import Thread
from apps.products.models import Product


class MaterialIssue(BaseModel):
    master = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'master'})
    issue_date = models.DateField(auto_now_add=True)
    thread = models.ForeignKey(Thread, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)  # Bu umumiy ip miqdori
    expected_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    expected_quantity = models.IntegerField(default=0, validators=[MinValueValidator(1)])
    is_closed = models.BooleanField(default=False)
    note = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Ip berish'
        verbose_name_plural = 'Ip berishlar'
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.master} - {self.expected_quantity} dona"

    @property
    def total_received_good_quantity(self):
        """Ushbu berilma uchun qabul qilingan yaroqli mahsulotlar"""
        return self.receipts.filter(quality_status=QualityStatus.GOOD).aggregate(
            total=Sum('quantity_received')
        )['total'] or 0

    @property
    def current_balance_quantity(self):
        """Ushbu berilma uchun qolgan qarz (hech qachon manfiy bo'lmaydi)"""
        debt = self.expected_quantity - self.total_received_good_quantity
        return max(debt, 0)

    @property
    def is_completed(self):
        return self.current_balance_quantity <= 0


class ProductReceipt(BaseModel):
    """Mahsulot qabul qilish"""
    material_issue = models.ForeignKey(
        MaterialIssue, on_delete=models.CASCADE, related_name='receipts',
        verbose_name='Ip berish'
    )
    receipt_date = models.DateField(auto_now_add=True, verbose_name='Sana')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Mahsulot')
    quantity_received = models.IntegerField(
        validators=[MinValueValidator(1)], verbose_name='Miqdor (dona)'
    )
    quality_status = models.CharField(
        max_length=20, choices=QualityStatus.choices, default=QualityStatus.GOOD,
        verbose_name='Sifat'
    )
    defect_reason = models.CharField(
        max_length=20, choices=DefectReason.choices, blank=True, null=True,
        verbose_name='Brak sababi'
    )
    defect_description = models.TextField(blank=True, verbose_name='Brak tavsifi')
    actual_weight_per_item = models.DecimalField(
        max_digits=10, decimal_places=3, validators=[MinValueValidator(0.001)],
        verbose_name="1 dona og'irligi (kg)"
    )
    note = models.TextField(blank=True, verbose_name='Izoh')

    class Meta:
        verbose_name = 'Mahsulot qabul qilish'
        verbose_name_plural = 'Mahsulot qabul qilishlar'
        ordering = ['-receipt_date']

    @property
    def total_weight(self):
        return self.quantity_received * self.actual_weight_per_item

    @property
    def currency(self):
        """Ustaning afzal valyutasi"""
        return self.material_issue.master.preferred_currency

    @property
    def total_payment(self):
        """Valyutaga qarab to'lov summasini qaytaradi"""
        if self.quality_status != QualityStatus.GOOD:
            return 0

        master = self.material_issue.master
        if master.preferred_currency == CurrencyType.USD:
            return self.quantity_received * self.product.weaving_price_usd
        return self.quantity_received * self.product.weaving_price_uzs

    def save(self, *args, **kwargs):
        if not self.actual_weight_per_item:
            self.actual_weight_per_item = self.product.standard_weight

        is_new = not self.pk
        super().save(*args, **kwargs)

        if is_new and self.quality_status == QualityStatus.GOOD:
            balance, _ = MasterBalance.objects.get_or_create(master=self.material_issue.master)
            balance.total_product_given += self.quantity_received
            balance.total_weight_given += self.total_weight

            # Valyutaga qarab to'lov qo'shiladi
            if self.currency == CurrencyType.USD:
                balance.total_payment_due_usd += self.total_payment
            else:
                balance.total_payment_due_uzs += self.total_payment
            balance.save()

            if self.material_issue.current_balance_quantity <= 0:
                self.material_issue.is_closed = True
                self.material_issue.save()

    def __str__(self):
        return f"{self.material_issue.master} - {self.quantity_received} dona"


class MasterBalance(BaseModel):
    """Usta balansi - ikki valyutada"""
    master = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='balance',
        limit_choices_to={'role': 'master'}, verbose_name='Usta'
    )

    # Ip olish
    total_thread_taken = models.DecimalField(
        max_digits=12, decimal_places=3, default=0,
        verbose_name='Jami olingan ip (kg)'
    )

    # Mahsulot topshirish
    total_product_given = models.IntegerField(default=0, verbose_name='Jami topshirilgan (dona)')
    total_weight_given = models.DecimalField(
        max_digits=15, decimal_places=3, default=0,
        verbose_name='Jami og\'irlik (kg)'
    )

    # To'lovlar - so'm
    total_payment_due_uzs = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        verbose_name="Jami to'lanadigan (so'm)"
    )
    total_payment_paid_uzs = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        verbose_name="To'langan (so'm)"
    )

    # To'lovlar - dollar
    total_payment_due_usd = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        verbose_name="Jami to'lanadigan (dollar)"
    )
    total_payment_paid_usd = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        verbose_name="To'langan (dollar)"
    )

    class Meta:
        verbose_name = 'Usta balansi'
        verbose_name_plural = 'Ustalar balanslari'

    def __str__(self):
        return f"{self.master}: {self.product_debt} dona qarz"

    @property
    def product_debt(self):
        """Joriy mahsulot qarzi (faqat yopilmagan berilmalar bo'yicha)"""
        active_issues = MaterialIssue.objects.filter(
            master=self.master,
            is_closed=False
        )

        total_expected = active_issues.aggregate(
            total=Sum('expected_quantity')
        )['total'] or 0

        # Qabul qilingan yaroqli mahsulotlar (faqat yopilmagan berilmalar uchun)
        total_received = 0
        for issue in active_issues:
            received = issue.receipts.filter(
                quality_status=QualityStatus.GOOD
            ).aggregate(Sum('quantity_received'))['quantity_received__sum'] or 0
            total_received += received

        debt = total_expected - total_received
        # Hech qachon manfiy bo'lmasligi kerak
        return max(debt, 0)

    @property
    def payment_balance_uzs(self):
        """So'mdagi qolgan qarz"""
        return self.total_payment_due_uzs - self.total_payment_paid_uzs

    @property
    def payment_balance_usd(self):
        """Dollardagi qolgan qarz"""
        return self.total_payment_due_usd - self.total_payment_paid_usd

    @property
    def payment_balance_display(self):
        """Ustaning valyutasida qolgan qarz"""
        if self.master.preferred_currency == CurrencyType.USD:
            return f"{self.payment_balance_usd:,.2f} USD"
        return f"{self.payment_balance_uzs:,.0f} so'm"

    @property
    def total_payment_due_display(self):
        """Ustaning valyutasida jami to'lanadigan"""
        if self.master.preferred_currency == CurrencyType.USD:
            return f"{self.total_payment_due_usd:,.2f} USD"
        return f"{self.total_payment_due_uzs:,.0f} so'm"

    @property
    def total_payment_paid_display(self):
        """Ustaning valyutasida to'langan"""
        if self.master.preferred_currency == CurrencyType.USD:
            return f"{self.total_payment_paid_usd:,.2f} USD"
        return f"{self.total_payment_paid_uzs:,.0f} so'm"

    @property
    def has_debt(self):
        return self.product_debt > 0 or self.payment_balance_uzs > 0 or self.payment_balance_usd > 0