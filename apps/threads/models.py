from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import BaseModel
from apps.core.constants import TransactionType
from apps.core.utils import validate_decimal_precision
from apps.core.constants import PaymentType  # yangi constant


class Thread(BaseModel):
    """
    Thread/Yarn model
    """
    name = models.CharField(max_length=100, verbose_name='Ip nomi')
    color = models.CharField(max_length=50, blank=True, verbose_name='Rangi')
    article = models.CharField(max_length=50, blank=True, verbose_name='Artikul')
    unit = models.CharField(max_length=10, default='kg', verbose_name="O'lchov birligi")
    price_per_unit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Narxi (1 kg)'
    )
    current_stock = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Joriy qoldiq'
    )
    min_stock_threshold = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=10,
        verbose_name='Minimal qoldiq chegarasi'
    )

    class Meta:
        verbose_name = 'Ip'
        verbose_name_plural = 'Iplar'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.color})" if self.color else self.name

    @property
    def is_low_stock(self):
        return self.current_stock <= self.min_stock_threshold

    @property
    def is_out_of_stock(self):
        return self.current_stock == 0

    def add_stock(self, quantity, note='', user=None):
        """Add stock to thread"""
        if quantity <= 0:
            raise ValueError('Miqdor 0 dan katta bo\'lishi kerak')

        self.current_stock += Decimal(str(quantity))
        self.save()

        ThreadTransaction.objects.create(
            thread=self,
            quantity=quantity,
            transaction_type=TransactionType.INCOMING,
            note=note,
            created_by=user
        )

    def remove_stock(self, quantity, note='', user=None):
        """Remove stock from thread"""
        if quantity <= 0:
            raise ValueError('Miqdor 0 dan katta bo\'lishi kerak')
        if quantity > self.current_stock:
            raise ValueError('Omborda yetarli ip mavjud emas')

        self.current_stock -= Decimal(str(quantity))
        self.save()

        ThreadTransaction.objects.create(
            thread=self,
            quantity=quantity,
            transaction_type=TransactionType.OUTGOING,
            note=note,
            created_by=user
        )




class ThreadTransaction(BaseModel):
    thread = models.ForeignKey(
        Thread, on_delete=models.CASCADE, related_name='transactions',
        verbose_name='Ip'
    )
    quantity = models.DecimalField(
        max_digits=12, decimal_places=3, validators=[MinValueValidator(0)],
        verbose_name='Miqdor'
    )
    transaction_type = models.CharField(
        max_length=20, choices=TransactionType.choices,
        verbose_name='Harakat turi'
    )
    related_master = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Tegishli usta'
    )
    note = models.TextField(blank=True, verbose_name='Izoh')
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_transactions', verbose_name='Yaratgan'
    )

    class Meta:
        verbose_name = 'Ip harakati'
        verbose_name_plural = 'Ip harakatlari'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()}: {self.thread.name} - {self.quantity} kg"


class ThreadSupplierDebt(BaseModel):
    """Ip yetkazib beruvchiga qarz"""
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, verbose_name='Ip')
    quantity = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='Miqdor (kg)')
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Qarz summasi')
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="To'langan")
    payment_type = models.CharField(max_length=20, default='credit')
    note = models.TextField(blank=True, verbose_name='Izoh')
    is_paid = models.BooleanField(default=False, verbose_name="To'liq to'langan")

    @property
    def remaining_amount(self):
        """Qolgan qarz"""
        if self.paid_amount is None:
            return self.amount
        return self.amount - self.paid_amount

    def save(self, *args, **kwargs):
        # Har safar saqlashda paid_amount ni tekshirish
        if self.paid_amount is None:
            self.paid_amount = 0

        # To'liq to'langanligini tekshirish
        if self.remaining_amount <= 0:
            self.is_paid = True

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.thread.name} - {self.quantity} kg - {self.remaining_amount:,.0f} so'm qarz"


class SupplierPayment(BaseModel):
    """Yetkazib beruvchiga to'lov"""
    debt = models.ForeignKey(ThreadSupplierDebt, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="To'lov summasi")
    note = models.TextField(blank=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Qarzni yangilash
        self.debt.paid_amount = (self.debt.paid_amount or 0) + self.amount
        if self.debt.paid_amount >= self.debt.amount:
            self.debt.is_paid = True
        self.debt.save()