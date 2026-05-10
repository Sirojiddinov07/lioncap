from datetime import datetime
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
    issue_date = models.DateField(default=datetime.now, verbose_name='Berilgan sana')  # auto_now_add olib tashlandi
    thread = models.ForeignKey(Thread, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)  # Bu umumiy ip miqdori
    expected_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    expected_quantity = models.IntegerField(default=0, validators=[MinValueValidator(1)])
    is_closed = models.BooleanField(default=False)
    note = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.pk and not self.issue_date:
            self.issue_date = datetime.now().date()
        super().save(*args, **kwargs)

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
    receipt_date = models.DateField(default=datetime.now, verbose_name='Qabul qilingan sana')
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

    def save(self, *args, **kwargs):
        if not self.pk and not self.receipt_date:
            self.receipt_date = datetime.now().date()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Mahsulot qabul qilish'
        verbose_name_plural = 'Mahsulot qabul qilishlar'
        ordering = ['-receipt_date']

    @property
    def total_weight(self):
        return self.quantity_received * self.actual_weight_per_item

    @property
    def total_payment(self):
        """To'lov summasi (faqat yaroqli mahsulot uchun)"""
        if self.quality_status == QualityStatus.GOOD:
            # Ustaning valyutasiga qarab to'lov
            master = self.material_issue.master
            if master.preferred_currency == 'usd':
                return self.quantity_received * self.product.weaving_price_usd
            else:
                return self.quantity_received * self.product.weaving_price_uzs
        return 0

    def save(self, *args, **kwargs):
        if not self.actual_weight_per_item:
            self.actual_weight_per_item = self.product.standard_weight

        is_new = not self.pk
        super().save(*args, **kwargs)

        if is_new and self.quality_status == QualityStatus.GOOD:
            # Usta balansini yangilash
            balance, _ = MasterBalance.objects.get_or_create(master=self.material_issue.master)
            balance.total_product_given += self.quantity_received
            balance.total_weight_given += self.total_weight

            # To'lov qo'shish (valyutaga qarab)
            master = self.material_issue.master
            if master.preferred_currency == 'usd':
                balance.total_payment_due_usd += self.total_payment
            else:
                balance.total_payment_due_uzs += self.total_payment
            balance.save()

            # Mahsulot omboriga qo'shish
            product = self.product
            product.stock_quantity += self.quantity_received
            product.save()

            # Ip berishni yopish
            if self.material_issue.current_balance_quantity <= 0:
                self.material_issue.is_closed = True
                self.material_issue.save()

    def __str__(self):
        return f"{self.material_issue.master} - {self.quantity_received} dona"



class MasterBalance(BaseModel):
    """Usta balansi"""
    master = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='balance',
        limit_choices_to={'role': 'master'}, verbose_name='Usta'
    )

    # Ip olish
    total_thread_taken = models.DecimalField(
        max_digits=12, decimal_places=3, default=0,
        verbose_name='Jami olingan ip (kg)'
    )

    # Mahsulot topshirish (yaroqli)
    total_product_given = models.IntegerField(default=0, verbose_name='Jami topshirilgan (dona)')
    total_weight_given = models.DecimalField(
        max_digits=15, decimal_places=3, default=0,
        verbose_name='Jami og\'irlik (kg)'
    )

    # Yaroqsiz mahsulotlar
    total_defective_product_given = models.IntegerField(default=0, verbose_name='Jami yaroqsiz (dona)')
    total_defective_weight_given = models.DecimalField(
        max_digits=15, decimal_places=3, default=0,
        verbose_name='Jami yaroqsiz og\'irlik (kg)'
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
        """Joriy mahsulot qarzi (faqat yopilmagan berilmalar bo'yicha) - hech qachon manfiy emas"""
        active_issues = MaterialIssue.objects.filter(
            master=self.master,
            is_closed=False
        )
        total_expected = active_issues.aggregate(
            total=Sum('expected_quantity')
        )['total'] or 0

        # Qabul qilingan mahsulotlar faqat ACTIVE berilmalar uchun
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
        return self.total_payment_due_uzs - self.total_payment_paid_uzs

    @property
    def payment_balance_usd(self):
        return self.total_payment_due_usd - self.total_payment_paid_usd

    @property
    def payment_balance_display(self):
        if self.master.preferred_currency == 'usd':
            return f"{self.payment_balance_usd:,.2f} USD"
        return f"{self.payment_balance_uzs:,.0f} so'm"

    @property
    def has_any_debt(self):
        """Ustada qarz borligini tekshiradi"""
        return self.product_debt > 0 or self.payment_balance_uzs > 0 or self.payment_balance_usd > 0

    @property
    def remaining_ip(self):
        """Ustaning qolgan ip miqdori (kg)"""
        return self.total_thread_taken - self.total_weight_given

    @property
    def is_ip_low(self):
        """Ip qoldig'i kamligini tekshirish (100 kg dan kam)"""
        return self.remaining_ip < 100